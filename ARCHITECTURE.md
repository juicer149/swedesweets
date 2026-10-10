# Architecture

SwedeSweets uses explicit boundaries between actor-facing interfaces,
sales-channel application policy, shared domain/application capabilities, and
application-wide composition.

The architecture is organized around four different kinds of responsibility:

```text
actor-facing interfaces
    business_portal
    storefront
    ops_portal

sales-channel applications
    business
    retail

shared domain/application capabilities
    accounts
    customers
    products
    pricing
    carts
    orders
    inventory
    reservations
    payments
    fulfillment

application-wide composition
    config
```

These are different axes.

An actor-facing application answers:

> Who is using this interface?

A sales-channel application answers:

> Which commercial rules apply to this transaction?

A shared capability answers:

> Which stable domain or application concept owns this state or behavior?

`config` answers:

> How is the whole Django application wired together?

The common dependency direction is:

```text
HTTP / presentation
        ↓
actor-facing use case
        ↓
sales-channel application when channel policy applies
        ↓
shared domain/application capability
        ↓
persistence
```

Not every use case needs every layer, but dependencies point inward.

Core domain and application code must not depend on the HTTP interface through
which it is used.

## Dependency direction

The main actor-facing applications are:

```text
business_portal
    authenticated B2B customer UI

storefront
    public retail UI

ops_portal
    internal staff UI
```

They may depend on the application layer that owns the use case.

Typical dependencies are:

```text
business_portal
        ↓
business
orders
customers
products
carts

storefront
        ↓
retail
carts
products
payments

ops_portal
        ↓
orders
inventory
products
customers
accounts
business
retail
shared capabilities
```

`ops_portal` is an actor-facing application, not a sales channel.

Staff may perform operations whose semantics belong to a specific sales
channel. In that case the portal should call the channel application rather
than duplicate its rules.

For example:

```text
ops_portal/orders
        ↓
business
        ↓
orders / pricing / reservations / inventory
```

is correct when staff are creating or placing a BUSINESS order.

Likewise, an operational retail workflow may legitimately call `retail` when
the operation is semantically RETAIL.

This does not violate dependency direction.

The prohibited direction is the reverse:

```text
business
    ✗→ ops_portal

orders
    ✗→ business_portal

retail
    ✗→ storefront

products
    ✗→ storefront
```

Application behavior should remain usable even if a particular HTTP interface
disappears.

## Actor and channel are separate axes

Do not infer sales-channel semantics from the actor.

Examples:

```text
B2B customer using business_portal
    usually invokes BUSINESS behavior

anonymous buyer using storefront
    invokes RETAIL behavior

staff using ops_portal
    may invoke BUSINESS behavior
    may invoke RETAIL behavior
    may invoke channel-neutral operational behavior
```

Authentication and sales channel are also separate.

Being logged in does not by itself determine:

```text
catalog
commercial offer
price requirements
reservation policy
payment behavior
fulfillment policy
```

Those decisions belong to channel policy and channel-specific application
behavior.

## Core code outside HTTP

Domain and application behavior should remain usable from:

```text
manage.py shell
management commands
workers
scheduled jobs
tests
other application services
```

Core logic should therefore not require:

```text
HttpRequest
templates
messages
URL routing
browser state
portal-specific view models
```

HTTP concerns belong at the edge.

## Actor-facing UI ownership

UI ownership follows the actor using the interface, not the domain object being
manipulated.

```text
business_portal
    authenticated B2B customer experience

storefront
    public retail experience

ops_portal
    internal staff experience
```

For example:

```text
ops_portal/products/
    staff-facing product management

products/
    product state
    product selectors
    product mutations
```

The actor-facing application owns:

```text
views
forms
actor-specific presentation
view models
templates
routes
navigation
HTTP orchestration
actor/object scoping at the edge
```

The domain or application capability owns:

```text
persistent business state
business invariants
domain queries
mutations
transactions
locking
channel policy
```

A portal may compose multiple application capabilities, but it must not become
a second implementation of their business rules.

## Portal organization

Actor-facing applications may be organized internally around stable actor use
cases.

For example:

```text
business_portal/
    catalog/
        views.py
        tests/

    orders/
        views.py
        presentation.py
        *_viewmodels.py
        repeat_services.py

    selectors.py
        portal-level actor scope

    views.py
        portal home and simple portal-level pages
```

This is not a second domain model.

`business_portal/orders` owns the B2B customer's order interface.

The order domain remains owned by:

```text
orders
```

Likewise:

```text
ops_portal/orders
    staff order interface

orders
    shared order state and lifecycle
```

Portal package structure should follow useful actor-facing use cases rather
than mechanically mirror every domain application.

## Actor-scoped UI cache

A portal may own a narrow, actor-specific model representing transient UI state
when that state:

```text
exists only to serve that actor's interface
is not domain truth
has no meaning to other actors or domain applications
can be deleted without losing business truth
```

Example:

```text
ops_portal/models.py
    PickChecklistMark
        caches which reserved pick lines staff have checked off
        during packing
```

The real order and reservation state still belongs to:

```text
orders
reservations
```

Portal-owned persistence of this kind should be rare.

Persisting a UI cache does not by itself justify creating a new domain
application.

## Domain and application modules

A domain/application package commonly contains:

```text
models.py
    persistent state and model-level invariants

selectors.py
    read-only queries and read models

services.py
    mutations, workflows and transactional invariants

errors.py
    domain/application failures

datatypes.py
    explicit input and result structures
```

Not every package needs every module.

A useful distinction is:

```text
selector
    asks the system something

service
    changes the system

view
    translates HTTP into application operations
```

Selectors should not mutate persistent state.

Services should own mutations and transactional behavior.

Views should remain thin HTTP orchestration.

## Read ownership

Persistence knowledge belongs to the application that owns the model.

Examples:

```text
orders/selectors.py
    knows how orders are queried

inventory/selectors.py
    knows how inventory batches are queried

products/selectors.py
    knows how products are queried

customers/selectors.py
    knows how customers are queried
```

Other applications may call these selectors.

They should avoid reproducing the same ORM knowledge when an owning selector
already exists.

A composing module owns the cross-domain use case.

Each domain retains ownership of how its own persistence is queried.

For example:

```text
accounts/activity_selectors.py
        ↓
orders/selectors.py
products/selectors.py
inventory/selectors.py
customers/selectors.py
```

## Actor and object scope

A portal may add actor-specific scoping on top of domain selectors.

For example:

```text
business_portal/selectors.py
    logged-in Django user
        ↓
    CustomerMembership
        ↓
    Customer
```

Keep these responsibilities separate:

```text
domain selector
    how domain objects are queried

portal scope
    which objects this actor may address
```

Capabilities answer:

> May this actor perform this kind of operation?

Object scope answers:

> May this actor address this specific object?

Both may be required.

Capability checks without object scoping are insufficient for actor-owned data.

## Write ownership

Mutations belong to the domain or application capability that owns the behavior
being changed.

Examples:

```text
orders/services.py
    generic order lifecycle

carts/services.py
    generic mutable-cart mechanics

inventory/services.py
    inventory mutations

customers/services.py
    customer mutations

accounts/services.py
    account lifecycle

business/cart_services.py
    BUSINESS cart ownership and channel policy

business/services.py
    BUSINESS order composition and placement

retail/services.py
    RETAIL checkout/payment application workflow
```

Actor-facing views may orchestrate these operations, but should not reproduce
their rules.

When an actor-facing use case needs channel semantics, prefer the channel
application:

```text
ops_portal
    ↓
business
    ↓
orders
```

rather than:

```text
ops_portal
    duplicates BUSINESS placement rules
```

## Transactions and locking

Transactional writes belong as close as practical to the mutation whose
invariants they protect.

Conceptually:

```text
HTTP request
    ↓
actor-facing view
    ↓
application/domain service
    ↓
transaction + locking
    ↓
database
```

HTTP views should not maintain database consistency themselves.

Lock the row that represents the serialization boundary for the invariant being
protected.

For example, generic cart mutations lock the parent `Cart` so concurrent line
mutations for the same cart are serialized.

## Accounts and authorization

`accounts` owns shared account identity and the capability language used across
the project.

Examples:

```text
accounts/models.py
    StaffAccount
    CustomerMembership

accounts/roles.py
    AccountRole
    StaffAccessLevel
    Capability
    RoleSpec

accounts/permissions.py
    Django User -> AccountRole -> RoleSpec

accounts/services.py
    account lifecycle mutations
```

Django authentication answers:

> Who is logged in?

`accounts` answers:

> What account identity does this user represent?

and:

> What capabilities does that identity have?

Authentication, account identity, authorization, sales channel and UI routing
are related but separate concepts.

## Shared account UI

Not every HTTP view belongs in an actor portal.

Shared authentication and self-account behavior may remain in `accounts` when
it is not specific to B2B customers, staff operations or retail storefront
behavior.

Actor-specific account administration belongs to the actor-facing portal.

For example:

```text
ops_portal/accounts
    staff-facing account administration

accounts
    shared identity, permissions and lifecycle
```

B2B customers use:

```text
/my/
```

as their canonical account area.

`/accounts/me/` remains a shared self-account route and may redirect B2B
customers into `business_portal`.

## Route structure

Top-level URL prefixes describe application surfaces:

```text
/
    public landing page

/shop/
    public retail storefront

/my/
    authenticated B2B customer area

/ops/
    internal staff operations

/accounts/
    shared authentication/account workflows
```

Operational resources live below `/ops/`, for example:

```text
/ops/orders/
/ops/customers/
/ops/inventory/
/ops/products/
/ops/accounts/
```

B2B customer routes live below `/my/`, including:

```text
catalog
cart
order review
order history
profile
customer-facing account behavior
```

The URL prefix is not an authorization boundary.

Capabilities, route policies and object scoping remain authoritative.

## Route authorization

Route access declarations live close to the routes they describe.

Application-wide access-policy composition belongs in:

```text
config/policies.py
```

Authorization is fail-closed.

Navigation is UX, not authorization.

A hidden link is not a security boundary.

The destination route must enforce its own access policy.

## Navigation

Navigation is actor-specific presentation.

Generic navigation primitives may live in:

```text
common/navigation.py
```

Actor-specific navigation belongs with the actor:

```text
business_portal/navigation.py
ops_portal/navigation.py
```

Application-wide composition belongs in:

```text
config/context_processors.py
```

Navigation should express what the UI offers.

It must not become an authorization mechanism.

## Composition root

`config` owns application-wide composition.

Examples:

```text
config/settings.py
    installed applications
    middleware
    global Django configuration

config/policies.py
    aggregate route access declarations

config/login_routing.py
    post-login destination selection

config/context_processors.py
    actor-specific navigation composition

config/middleware.py
    global request/session behavior

config/urls.py
    top-level URL composition
```

`config` may know about multiple applications because wiring the whole
application together is its responsibility.

A domain application should not become the composition root for unrelated
applications.

## Presentation

Actor-specific presentation belongs to the actor-facing application.

Examples:

```text
business_portal
    B2B order labels
    cart presentation
    order cards
    customer-facing links/actions

ops_portal
    operational status/actions
    staff-facing forms
    packing presentation

storefront
    retail catalog/cart/checkout presentation
```

Neutral helpers may remain near a domain when they do not know about a specific
actor.

For example:

```text
products/localization.py
    channel-neutral product-name localization
```

while:

```text
business_portal/orders/product_presentation.py
    B2B-specific product presentation
```

belongs to the portal.

Prefer small duplication over premature cross-portal abstractions.

Similar HTML or labels do not automatically represent the same abstraction.

## Shared UI primitives

Reusable actor-neutral UI primitives may live in:

```text
common/
```

Examples include:

```text
table controls
detail cards
page headers
generic UI dataclasses
form-layout helpers
navigation primitives
sales-channel enum
```

Actor-specific:

```text
copy
labels
URLs
actions
workflows
authorization meaning
```

should remain in the owning portal.

## Sales channels

The project currently has two sales channels:

```text
BUSINESS
RETAIL
```

The shared channel value lives in:

```text
common.channels.SalesChannel
```

Channel applications own policy:

```text
business
    BUSINESS catalog/cart/order rules

retail
    RETAIL catalog/cart/checkout/payment rules
```

Shared capabilities should not infer channel behavior from authentication or
from which portal invoked them.

## Customer identity

A persistent:

```text
Customer
```

represents a business/customer entity.

It is not synonymous with:

```text
Django User
shopping session
anonymous retail buyer
individual order
```

An anonymous retail checkout does not require a persistent `Customer`.

Retail orders preserve required buyer information through order snapshots.

## Products and inventory

Product identity and physical stock are separate concepts.

```text
Product
    stable SKU/product identity

ProductVariant
    one size, weight or kind of a product; every product has at least one
    (docs/product-variants.md); batches, prices and order lines move to it
    step by step

InventoryBatch
    physical stock
    quantity
    expiry
    location
```

Product identity should not encode individual stock batches.

`products` owns product identity and neutral product behavior.

`inventory` owns physical inventory state and inventory mutations.

## Pricing and commercial offers

`pricing` owns commercial offers and current price data.

The current model names are:

```text
CommercialPrice
PriceAmount
```

`CommercialPrice` is semantically the persistent commercial offer identity.

`PriceAmount` is current monetary price data attached to that offer.

Keep these concepts separate:

```text
commercial offer identity
    what commercial option was selected

current price data
    what that offer costs now

historical order price
    what was snapshotted when the order was created

physical fulfillment
    which inventory batches were actually reserved/picked
```

Conceptually:

```text
Product
    stable product identity

CommercialPrice
    persistent offer identity
    one sales channel
    product-wide or batch-specific scope
    enabled/disabled channel availability

PriceAmount
    current amount in one currency
```

An offer that references an inventory batch describes the commercial scope of
the offer.

It does not by itself prove that the same batch was physically reserved or
picked.

Physical truth belongs to:

```text
reservations.Allocation
```

### BUSINESS standard offers

Every buyable BUSINESS product has an explicit persistent standard offer:

```text
CommercialPrice
    channel = BUSINESS
    product = product
    batch = NULL
```

The standard offer is not synthesized in memory.

A product without a BUSINESS standard offer is not sold to business customers
at the standard price, exactly like one whose offer is disabled: the business
catalogue leaves it out (batch-specific BUSINESS offers may still list it) and
ordering it is rejected as an invalid order. Products are channel-neutral
labels; each channel's offers decide where a product is sold, so a product may
be sold in BUSINESS, RETAIL, both (possibly at different prices) or neither.

Its `PriceAmount` may be absent because BUSINESS standard orders may be invoiced
later.

BUSINESS batch-specific offers require the channel's configured concrete price
policy, currently EUR pricing.

Existing offers are not implicitly re-enabled.

Availability changes go through the pricing/application service responsible for
that mutation.

### RETAIL offers

Retail offers are explicit commercial decisions.

A RETAIL offer used for checkout requires a valid concrete price according to
retail policy.

## Stock-pool semantics

A product-wide offer and a batch-specific offer must not simultaneously expose
the same physical units as independently selectable stock.

The stock-pool invariant is:

```text
A batch is excluded from a product-wide offer's pool
if and only if its own batch offer is orderable
in the same channel.
```

A disabled or otherwise non-orderable batch offer leaves that batch in the
product-wide pool.

`list_orderable_batches_for_offer` resolves the physical batches that may back
one offer.

It is deliberately reservation-agnostic: it answers physical eligibility, not
remaining reservable quantity.

Reservation accounting belongs downstream in `reservations`, where rows are
locked and available quantity is calculated safely.

Catalog presentation may layer reservation-adjusted availability on top of the
shared pool mechanics.

A catalog is therefore an approximate:

> orderable right now

view.

Placement or payment re-validates authoritatively under transaction and
locking.

## Carts

`carts` owns generic mutable purchase intent.

Core models:

```text
Cart
    UUID identity
    sales channel
    timestamps

CartLine
    cart
    commercial_price
    quantity
    timestamps
```

Important invariants include:

```text
quantity > 0

one CommercialPrice at most once per Cart

Cart.channel == CartLine.commercial_price.channel
```

Generic cart mutations serialize on the parent `Cart`.

Conceptually:

```text
lock Cart
    ↓
validate generic cart invariant
    ↓
mutate CartLine rows
```

This avoids races between concurrent mutations of lines belonging to the same
cart.

### What generic carts do not own

`carts` deliberately does not decide:

```text
whether Product.active is required
whether an offer is currently enabled
whether a current PriceAmount is required
whether stock is available
whether an order limit is exceeded
whether payment is required
whether a reservation can be made
```

Those are channel/application policies.

This keeps `carts` small and reusable.

## BUSINESS cart ownership

The `business` application attaches one active generic cart to one business
customer through `BusinessCart`.

Conceptually:

```text
Customer
    1
    │
    1
BusinessCart
    │
    1
    ▼
Cart(channel=BUSINESS)
    │
    *
    ▼
CartLine
```

The current invariant is one active BUSINESS cart per customer.

`BusinessCart` owns only the association between business-customer identity and
the generic cart.

Mutable cart contents remain owned by `carts`.

Creating or resolving the customer's cart belongs to `business`, because the
customer ownership rule is BUSINESS-specific.

## BUSINESS cart policy

Adding an offer to a BUSINESS cart validates mutable-cart eligibility.

Current cart-stage rules include:

```text
offer.channel == BUSINESS
offer.enabled
offer.product.active

batch-specific BUSINESS offer
    requires current EUR price
```

Cart-stage mutation intentionally does not make stock availability or order
limits part of generic cart persistence.

Those constraints may change between browsing and placement.

They are therefore authoritatively revalidated when the cart becomes an order.

## Cart and order lifecycle

A cart and an order are different concepts.

```text
Cart
    mutable purchase intent

Order(DRAFT)
    durable transaction attempt

Order(PLACED)
    accepted durable order
```

The lifecycle is:

```text
Cart
  add / set quantity / remove / clear
              │
              ▼
        create Order(DRAFT)
              │
         ┌────┴────┐
         ▼         ▼
       place     discard
         │
         ▼
    Order(PLACED)
```

The old design treated a BUSINESS `Order(DRAFT)` as a shopping basket.

That is no longer allowed.

Generic order services do not expose line-level mutable-cart operations such as:

```text
add draft line
replace draft lines
set draft line quantity
remove draft line
```

Mutable shopping behavior belongs to `Cart`.

`Order(DRAFT)` exists only as a short-lived durable transaction attempt that can
be prepared, placed or discarded.

## BUSINESS cart placement

BUSINESS placement composes channel policy with generic order lifecycle
services.

Conceptually:

```text
Customer's BUSINESS Cart
        ↓
lock and read cart
        ↓
revalidate BUSINESS offers
        ↓
revalidate current business policy
        ↓
build resolved OrderDraft
        ↓
orders.create_draft_order
        ↓
prepare BUSINESS placement
    order limits
    stock/reservation rules
    other placement invariants
        ↓
orders.place_order
        ↓
clear Cart only after success
```

The operation is transactional.

If order creation, reservation, validation or placement fails, the transaction
rolls back and the customer's cart remains intact.

The cart is cleared only after successful placement.

This gives the system a clear ownership boundary:

```text
before successful placement
    mutable intent belongs to Cart

during transaction attempt
    durable candidate belongs to Order(DRAFT)

after success
    durable purchase belongs to Order(PLACED)
```

## Retail cart and checkout

Retail also uses the generic cart representation for mutable purchase intent.

The storefront owns retail HTTP/UI behavior.

`retail` owns retail application policy and checkout/payment workflow.

Conceptually:

```text
storefront
    ↓
retail cart policy
    ↓
carts
```

At checkout, retail resolves the cart into a durable RETAIL order with:

```text
Order(DRAFT)
OrderLine.commercial_offer
OrderLine.unit_price_snapshot
buyer snapshot
```

Retail payment startup revalidates retail availability and obtains temporary
reservations before an external payment attempt proceeds.

The provider/payment lifecycle belongs to `payments` plus retail workflow
composition, not to `carts`.

## Orders

`orders` owns the shared durable order model and generic order lifecycle.

It is not the owner of one particular actor interface or sales channel.

The same order capability may be used by:

```text
business
retail
business_portal
ops_portal
fulfillment
payments
```

Actor-specific presentation and HTTP behavior stay outside `orders`.

Core order responsibilities include:

```text
Order state
OrderLine state
buyer snapshots
price snapshots
generic lifecycle transitions
generic order persistence
generic commercial-offer consistency checks
```

### Order(DRAFT)

`Order(DRAFT)` is a durable transaction attempt.

It is not a mutable shopping cart.

Its intended lifecycle is:

```text
create
    ↓
prepare
    ↓
place

or

create
    ↓
discard
```

Channel applications may construct a resolved draft and ask `orders` to persist
it.

After creation, generic order services do not expose shopping-cart-style
line mutations.

### Durable commercial identity

Every current-schema `OrderLine` has a non-null:

```text
OrderLine.commercial_offer
```

This is the persistent identity of the commercial offer selected for that line.

There are no current runtime side tables such as:

```text
BusinessOfferSelection
RetailOfferSelection
```

Those models exist only in historical migration state where needed to backfill
older data.

### Price snapshot

Historical monetary truth lives on:

```text
OrderLine.unit_price_snapshot
```

Do not derive the historical charged or invoiced price from current
`PriceAmount`.

The offer identity and price snapshot serve different purposes:

```text
commercial_offer
    which commercial option was selected

unit_price_snapshot
    what monetary value was recorded for the order at that time
```

### Commercial scope is not fulfillment truth

A batch-specific `commercial_offer` does not itself mean that the referenced
batch was physically allocated.

Actual reservation/picking truth belongs to:

```text
reservations.Allocation
```

## Business channel

`business` owns BUSINESS-specific application behavior that is more than
presentation.

Examples include:

```text
BUSINESS catalog eligibility
BUSINESS cart ownership
BUSINESS cart mutation policy
BUSINESS order-draft construction
BUSINESS placement preparation
BUSINESS order-limit policy
BUSINESS reservation composition
```

Typical dependency direction:

```text
business_portal
        ↓
business
        ↓
carts
orders
pricing
products
inventory
reservations
customers
```

Operational staff may also invoke BUSINESS behavior:

```text
ops_portal
    ↓
business
```

when the use case is semantically a BUSINESS transaction.

This is preferable to duplicating BUSINESS rules in `ops_portal`.

A direct BUSINESS draft/order construction service may therefore legitimately
be used by operational workflows even though the B2B customer-facing shopping
flow uses `Cart`.

The distinction is:

```text
customer shopping intent
    -> Cart

durable BUSINESS transaction attempt
    -> Order(DRAFT)
```

## Retail channel

`retail` owns RETAIL-specific application behavior and policy.

Examples include:

```text
retail catalog eligibility
retail cart policy
anonymous buyer validation
retail checkout
retail order creation
retail reservation policy
payment-start workflow
payment reconciliation/recovery composition
```

The public HTTP interface belongs to:

```text
storefront
```

Conceptually:

```text
storefront
    public HTTP/UI
        ↓
retail
    RETAIL application policy
        ↓
carts
orders
pricing
reservations
payments
products
inventory
```

Retail application behavior should remain usable without a browser request.

## Shared capabilities

Capabilities meaningful across actors or channels remain separate from
actor-facing portals.

Examples:

```text
reservations
    stock-reservation state and mechanism

payments
    payment state and provider integration

fulfillment
    shared pick/pack application workflows
```

A shared capability should exist because it represents a stable application
concept, not merely because two callers contain similar code.

## Reservations

`reservations` owns reservation state and reservation mechanics.

It owns:

```text
Allocation
```

a batch-level claim on physical stock made on behalf of one order line.

The physical database table retains its historical name:

```text
orders_allocation
```

through `db_table`.

Application ownership is nevertheless `reservations`.

Dependency direction:

```text
reservations
    ↓
orders
inventory
```

`orders` must not import `reservations`.

An `Allocation` cannot exist without an order line and an inventory batch.

An `Order` may exist without allocations.

This asymmetry is intentional.

Reservations are a capability applied to an order, not part of generic order
identity.

## Payments

Payment processing is a capability separate from retail presentation.

```text
payments
    payment records
    provider integration
    payment services
    provider callbacks/webhooks

retail
    retail payment workflow and policy

storefront
    public payment-return UI
```

Not all HTTP endpoints are actor-facing pages.

Machine-to-machine provider callbacks may legitimately live with the capability
they serve.

## Billing

Payment execution and billing/invoicing are different concepts.

Future billing behavior should not be added to `payments` merely because money
is involved.

Conceptually:

```text
payments
    payment execution and provider state

billing
    invoices
    billing snapshots
    accounting-facing billing concepts
```

Introduce a `billing` application only when that stable capability actually
exists.

## Fulfillment

`fulfillment` is a shared application capability.

It composes order and reservation data into fulfillment workflows.

Examples include:

```text
PickLine
get_packaging_list
get_packed_lines
```

Reservation state remains owned by `reservations`.

Conceptually:

```text
fulfillment
    ↓
orders
inventory
reservations
```

`fulfillment` should not own actor-specific staff pages.

Staff fulfillment UI belongs in:

```text
ops_portal
```

## Avoid synthetic symmetry

Do not create applications merely to make the package tree symmetrical.

For example, `ops_portal` does not need a generic `ops` application simply
because:

```text
business_portal
    uses business
```

Staff-facing code should call the application that owns the actual use case.

Examples:

```text
ops_portal
    ↓
orders

ops_portal
    ↓
inventory

ops_portal
    ↓
business
```

depending on whether the use case is:

```text
generic order behavior
inventory behavior
BUSINESS-channel behavior
```

Create a new application only when a stable concept with its own state,
invariants or policy emerges.

## Avoid premature catalog abstraction

Do not create a generic `catalog` application merely because more than one
channel displays products.

Today:

```text
products
    neutral product identity and behavior

business
    BUSINESS catalog eligibility/policy

business_portal
    B2B catalog presentation

retail
    RETAIL catalog eligibility/policy

storefront
    retail catalog presentation
```

A shared catalog application would only be justified if a stable,
channel-neutral catalog capability emerges.

## Architecture tests

Architecture tests should protect dependency direction and important ownership
rules.

Useful invariants include:

```text
orders must not import reservations

domain/application packages must not import actor-facing portals

config may compose multiple applications

actor-facing portals may import channel applications

ops_portal may import business/retail when invoking channel semantics

historical migration models are not current runtime APIs
```

When deciding whether a dependency is acceptable, ask:

> Which side owns the invariant being used?

and:

> Could the called behavior still work if this HTTP interface disappeared?

If the answer to the second question is no, presentation or HTTP concerns may
have leaked inward.

## Good and suspicious dependency examples

Good:

```text
business_portal
    ↓
business

storefront
    ↓
retail

ops_portal
    ↓
business

ops_portal
    ↓
orders

business
    ↓
orders

retail
    ↓
payments

reservations
    ↓
orders
inventory

config
    ↓
multiple applications
```

Suspicious:

```text
business
    ↓
business_portal

retail
    ↓
storefront

orders
    ↓
ops_portal

products
    ↓
business_portal

inventory
    ↓
ops_portal
```

The actor-facing edge may depend inward.

Core/application code should not depend outward on an actor-specific interface.

## Current application boundaries

Actor-facing interfaces:

```text
business_portal
    authenticated B2B customer interface

storefront
    public retail interface

ops_portal
    internal staff interface
```

Sales-channel applications:

```text
business
    BUSINESS policy and application workflows

retail
    RETAIL policy and application workflows
```

Shared domain/application capabilities:

```text
accounts
customers
products
pricing
carts
orders
inventory
reservations
payments
fulfillment
```

Application-wide composition:

```text
config
```

Internal staff UI is currently organized as:

```text
ops_portal/accounts
ops_portal/customers
ops_portal/products
ops_portal/inventory
ops_portal/orders
```

The corresponding state and business behavior remain in their owning
applications.

The B2B customer surface includes:

```text
business_portal/catalog
    B2B catalog UI

business_portal/orders
    cart UI
    cart mutation endpoints
    review/placement UI
    repeat-order UI
    order history/detail
    B2B order presentation

business_portal
    home/profile/navigation/actor scope
```

The retail HTTP surface is:

```text
storefront
```

while retail policy remains in:

```text
retail
```

Application-wide composition remains in:

```text
config
```

## Current route surfaces

The main route surfaces are:

```text
/
    public landing

/shop/
    retail storefront

/my/
    B2B customer area

/ops/
    internal operations

/accounts/
    shared authentication/account workflows
```

`/accounts/me/` remains a generic self-account route for shared/staff behavior.

B2B customers may be redirected from it to `/my/`.

## Adding new functionality

When introducing a feature, first identify the responsibility.

Ask:

```text
Is this actor-facing HTTP or presentation?
    -> business_portal / storefront / ops_portal

Is this BUSINESS-specific policy or workflow?
    -> business

Is this RETAIL-specific policy or workflow?
    -> retail

Is this mutable purchase intent?
    -> carts, plus channel policy in business/retail

Is this durable order state or generic order lifecycle?
    -> orders

Is this current offer/price data?
    -> pricing

Is this physical stock?
    -> inventory

Is this a claim against physical stock?
    -> reservations

Is this payment/provider state?
    -> payments

Is this shared pick/pack workflow?
    -> fulfillment

Is this persistent customer/account state?
    -> customers / accounts

Is this application-wide wiring?
    -> config
```

Then ask:

```text
Who owns the invariant?
Who owns the persistence?
Who owns the actor-specific presentation?
Which layer should know about the sales channel?
```

The location should follow from responsibility.

It should not be chosen merely because a nearby module is convenient to edit.

## Design rules

Prefer:

```text
explicit dependencies
one owner for each kind of truth
domain-owned persistence knowledge
selector-owned reads
service-owned mutations
thin HTTP orchestration
actor-owned presentation
channel-owned commercial policy
explicit object scoping
fail-closed authorization
transactional invariant enforcement
small modules with one clear responsibility
stable shared capabilities
```

Avoid:

```text
core/application imports from actor-facing portals
business rules in templates
business rules duplicated in views
ORM knowledge duplicated across applications
navigation used as authorization
actor-specific presentation in core modules
domain applications acting as global composition roots
sales-channel policy inferred from authentication
Order(DRAFT) used as a shopping cart
duplicate commercial-offer identity tables
current price used as historical order price
commercial offer scope treated as physical allocation truth
generic abstractions created only to remove small duplication
new applications created only for structural symmetry
```

## Guiding principle

The intended dependency shape is:

```text
HTTP / presentation
        ↓
actor-facing use case
        ↓
sales-channel application when channel policy applies
        ↓
shared domain/application capability
        ↓
persistence
```

Not every path uses every layer.

For a channel-neutral staff operation:

```text
ops_portal
    ↓
orders
```

may be enough.

For a BUSINESS-channel staff operation:

```text
ops_portal
    ↓
business
    ↓
orders / pricing / reservations
```

is appropriate.

For mutable purchase intent:

```text
business_portal or storefront
        ↓
business or retail
        ↓
carts
```

For durable purchase state:

```text
business or retail
        ↓
orders
```

The core ownership model is:

```text
CartLine.commercial_price
    mutable commercial intent

OrderLine.commercial_offer
    durable commercial identity

OrderLine.unit_price_snapshot
    historical monetary truth

reservations.Allocation
    physical stock / fulfillment truth
```

The purpose of these boundaries is not to maximize the number of modules.

The purpose is to make ownership obvious, change local, dependencies explicit,
business rules reusable, invalid states difficult to represent, and
historical, commercial and physical truth difficult to confuse.
