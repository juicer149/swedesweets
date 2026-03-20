# User creation
n+ = "is a positive integral"
su = "supplier"
st = "store"

NewUser = User( id   = n+
            username = "",
            pw_hash  = ...
            role     = su V st 
            )

let NewUser.role be st. When a NewStore is requested a notis (via mail) is sent
to the choosen supplier account for acceptance. 
Only User.role == st is available threw the website. To create a su you go in to the server or talk to the technical staff.

When supplier have accepted the request a mail i sent back to the store with
login credentials to use for the first login. 
The next step in the pipeline is the tranformations to a Store objects witch will hold the same id (UUID) as the corresponding User object.

# might not have name in user but only here 
NewStore = Store(
                id = NewUser.id,
                name = NewUser.name,
    # for now only France, could be a own table in the future
                address = "address",
                delivery_window = chosen period if they want automatic refill.
                )

This object should hold info avaible for the store to change:
    - Address for deliviery
    - contact info
    - 0 < delivery_window < exp_date or None
    - choose a sortement

sortement is the choosen products from the suppliers catalog. A store can choose a few diffrent standard sortements as starters, or the store can choose its own sortement, or alter the standard sortement. This will be stored as history and the store can uppdate or change its sortement at any given time to add or remove products.

Duo to the fact that its weighed candy some kind of controll will also be needed for symetri between the stand where the candy is stored for the customers and total amount of products so no box is empty or otherwise might have to have the same products in two diffrent containers. 




