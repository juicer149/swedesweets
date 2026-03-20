SwedeSweets är ett bolag som importerat och säljer lösgodis i Frankrike, mer specifikt Chamonix och omkringliggande byar och städer. Bolaget ansvarar för att fylla på och fälja lösgodis, men även chips från estrella och OLW i butikerna. 

Problem: 
Bolaget tar idag beställningar via SMS och mail, vilket är tidskrävande och kräver överdriven kommunikation mellan säljare och butik. Det är svårt att hålla koll på beställningar, och det finns en risk för misstag i kommunikationen.

Lösning:
För att effektivisera beställningsprocessen och minska risken för misstag ska en hemsida utvecklas där butikerna kan ha ett eget konto där de kan lägga in sina beställningar. SwedeSweets kan sedan enkelt se och hantera beställnignarna via en administratörspanel. Bolaget vill även att hemsidan ska se professionell ut och vara lätt att använda för både butikerna och administratörerna. 



Problem statement:
    - Ostrukturerad beställningsprocess via SMS och mail
    - Ingen historik över beställningar.
    - Ingen leveransstatus eller spårning av beställningar.
    - Svårt att skala upp verksamheten med nuvarande process.

Mål för v0.1.0:

@dataclass
class User:
    id: UUID
    username: str
    password: bytes # hashed password
    role: str # "admin" eller "store"
    sortiment: List[Product] # butikerna kan ha olika sortement

    - Ingen registrering av användare, butikerna kan skicka en request kring
      att få ett konto via hemsidan. Därefter kan SwedeSweets manuellt skapa
      kontot och skicka inloggningsuppgifter till butiken. Detta kan i sig vara
      autmatiserat via att SwedeSweets får en notis när en butik skickar en
      request för att kontrollera giltligheten av butiken innan kontot skapas.
      Detta minimerar risken för att obehöriga får tillgång till systemet.

    - Butikerna kan sedan logga in och då skapa sitt sortement via en katalog.
      Standard sortement kan väljas som start. Olika kategorier av produkter 
      beroende på butikstyp eller storlek. Dessa finns lagrade och behöver 
      !KOPIERAS! som data och inte länkas. Detta säkerställer att historik 
      eller data inte ändras när sortementet uppdateras. Butikerna kan sedan
      redigera sitt eget sortement genom att lägga till eller ta bort produkter
      Detta gör det enkelt för butikerna att anpassa sitt sortement efter deras
      behov och preferenser. I framtida verionser kan även maskininlärning
      användas för att ge rekommendationer baserat på tidigare mönster under
      olika perioder eller regioner.

    - Butikerna själva ska kunna klicka i en lista för vilka sorter som
      antingen behöver fyllas på eller inte fyllas på för att leverantören 
      enkelt ska kunna se vilka produkter som tas med i leveransen.

## Själva produkten:

@dataclass
class Product:
    id: UUID
    name: str # ex. "Cola nappar"
    expiration_date: date # hårt värde för oöppnad låda, ej relevant för butiker
    recommended_shelf_life: int # olika produkters kvalitet kan variera
    category: str # ex. "Lösgodis", "Chips", "Dryck"

