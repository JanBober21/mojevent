# Skrypt do zaladowania 10 testowych restauracji/sal weselnych
# dla uzytkownika FatBob.
# Uruchom: python populate_fatbob.py
import os, sys, django, random
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from datetime import time
from decimal import Decimal
from django.contrib.auth.models import User
from bookings.models import (
    Restaurant, RestaurantOwner, Menu, MenuItem, Review, UserProfile,
)

# ── 1. Utwórz użytkownika FatBob ─────────────────────────────────────────
user, created = User.objects.get_or_create(
    username="fatbob",
    defaults={
        "first_name": "Fat",
        "last_name": "Bob",
        "email": "fatbob.events@gmail.com",
    },
)
if created:
    user.set_password("Walkingdead1")
    user.save()
    print("✅ Użytkownik fatbob utworzony")
else:
    print("ℹ️  Użytkownik fatbob już istnieje")

# Profil
profile, _ = UserProfile.objects.get_or_create(
    user=user,
    defaults={"phone": "+48 512 345 678", "city": "Poznań"},
)

# ── 2. Dane 10 restauracji ───────────────────────────────────────────────
RESTAURANTS = [
    {
        "name": "Pałac Wąsowo",
        "description": (
            "Pałac Wąsowo to elegancki obiekt weselny w województwie wielkopolskim, "
            "położony niedaleko Nowego Tomyśla z dogodnym dojazdem z Poznania dzięki "
            "autostradzie A2. Piękne wnętrza sali weselnej, profesjonalna obsługa "
            "oraz wykwintna kuchnia tworzą idealne warunki na niezapomniane wesele."
        ),
        "address": "Wąsowo 59, 64-316 Kuślin",
        "city": "Poznań",
        "phone": "+48 61 44 12 100",
        "email": "recepcja@palacwasowo.pl",
        "website": "https://palacwasowo.pl",
        "max_guests": 150,
        "price_per_person": Decimal("290.00"),
        "has_parking": True,
        "has_garden": True,
        "has_dance_floor": True,
        "has_accommodation": True,
        "latitude": Decimal("52.3625"),
        "longitude": Decimal("16.3987"),
        "show_calendar": True,
        "hours": ("10:00", "22:00"),
        "image_url": "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800",
    },
    {
        "name": "Dworek Separowo",
        "description": (
            "Dworek Separowo to piękny obiekt weselny położony tuż obok Jeziora "
            "Strykowskiego. Oferuje śliczną salę weselną w otoczeniu natury, "
            "doskonałe jedzenie oraz romantyczną atmosferę idealne na wesela plenerowe."
        ),
        "address": "Separowo 1, 62-002 Suchy Las",
        "city": "Poznań",
        "phone": "+48 61 811 60 55",
        "email": "kontakt@dworekseparowo.pl",
        "website": "https://dworekseparowo.pl",
        "max_guests": 120,
        "price_per_person": Decimal("315.00"),
        "has_parking": True,
        "has_garden": True,
        "has_dance_floor": True,
        "has_accommodation": True,
        "latitude": Decimal("52.4810"),
        "longitude": Decimal("16.8945"),
        "show_calendar": True,
        "hours": ("11:00", "23:00"),
        "image_url": "https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?w=800",
    },
    {
        "name": "Hotel Remes Sport & Spa",
        "description": (
            "Czterogwiazdkowy hotel w Opalenicy oferujący świetne sale weselne, "
            "doskonały zespół pracowników i pyszne weselne jedzenie. "
            "Kompleks ze strefą SPA, basenem i nowoczesnymi pokojami."
        ),
        "address": "ul. Poznańska 96, 64-330 Opalenica",
        "city": "Poznań",
        "phone": "+48 61 44 77 100",
        "email": "wesela@hotelremes.pl",
        "website": "https://hotelremes.pl",
        "max_guests": 250,
        "price_per_person": Decimal("350.00"),
        "has_parking": True,
        "has_garden": True,
        "has_dance_floor": True,
        "has_accommodation": True,
        "latitude": Decimal("52.3100"),
        "longitude": Decimal("16.4050"),
        "show_calendar": False,
        "hours": ("09:00", "23:00"),
        "image_url": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=800",
    },
    {
        "name": "Stary Kamionek",
        "description": (
            "Klimatyczny obiekt pod Gnieznem oferujący salę balową dla 140 osób "
            "oraz pokoje gościnne w oryginalnym stylu. Otoczony terenem zielonym "
            "idealnym na śluby cywilne w plenerze i sesje zdjęciowe."
        ),
        "address": "Kamionek 5, 62-200 Gniezno",
        "city": "Poznań",
        "phone": "+48 61 426 15 30",
        "email": "info@starykamionek.pl",
        "website": "https://starykamionek.pl",
        "max_guests": 140,
        "price_per_person": Decimal("300.00"),
        "has_parking": True,
        "has_garden": True,
        "has_dance_floor": True,
        "has_accommodation": True,
        "latitude": Decimal("52.5350"),
        "longitude": Decimal("17.5930"),
        "show_calendar": True,
        "hours": ("12:00", "00:00"),
        "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800",
    },
    {
        "name": "Rio Grande Moments",
        "description": (
            "Wyjątkowy obiekt położony w malowniczej otulinie Wielkopolskiego "
            "Parku Narodowego w Krosinku. Nowoczesna sala weselna na 200 osób "
            "z panoramicznymi oknami i dostępem do ogrodu."
        ),
        "address": "Krosinko, ul. Wiejska 51, 62-050 Mosina",
        "city": "Poznań",
        "phone": "+48 61 813 24 00",
        "email": "events@riogrande.pl",
        "website": "https://riograndemoments.pl",
        "max_guests": 200,
        "price_per_person": Decimal("300.00"),
        "has_parking": True,
        "has_garden": True,
        "has_dance_floor": True,
        "has_accommodation": False,
        "latitude": Decimal("52.2515"),
        "longitude": Decimal("16.7905"),
        "show_calendar": True,
        "hours": ("10:00", "01:00"),
        "image_url": "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=800",
    },
    {
        "name": "Pałacyk Pod Lipami",
        "description": (
            "Obiekt weselny w Swarzędzu koło Poznania. Elegancka sala na 80 osób, "
            "kameralna atmosfera, piękny ogród z lipami i doskonała kuchnia. "
            "Idealny na mniejsze, intymne wesela."
        ),
        "address": "ul. Dworcowa 10, 62-020 Swarzędz",
        "city": "Poznań",
        "phone": "+48 61 651 22 33",
        "email": "rezerwacje@palacykpodlipami.pl",
        "website": "https://palacykpodlipami.pl",
        "max_guests": 80,
        "price_per_person": Decimal("115.00"),
        "has_parking": True,
        "has_garden": True,
        "has_dance_floor": True,
        "has_accommodation": True,
        "latitude": Decimal("52.4070"),
        "longitude": Decimal("17.0830"),
        "show_calendar": False,
        "hours": ("11:00", "22:00"),
        "image_url": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800",
    },
    {
        "name": "Hotel Poznański",
        "description": (
            "Doskonałe miejsce w Luboniu pod Poznaniem. Dwie przestrzenie weselne: "
            "elegancka sala restauracyjna i namiot bankietowy. Profesjonalna obsługa, "
            "własna kuchnia i parking na 45 samochodów."
        ),
        "address": "ul. Armii Poznań 30, 62-030 Luboń",
        "city": "Poznań",
        "phone": "+48 61 810 20 70",
        "email": "hotel@hotelpoznanski.pl",
        "website": "https://hotelpoznanski.pl",
        "max_guests": 220,
        "price_per_person": Decimal("229.00"),
        "has_parking": True,
        "has_garden": False,
        "has_dance_floor": True,
        "has_accommodation": True,
        "latitude": Decimal("52.3390"),
        "longitude": Decimal("16.8780"),
        "show_calendar": True,
        "hours": ("08:00", "23:00"),
        "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800",
    },
    {
        "name": "Hotel Lord Warszawa",
        "description": (
            "Prestiżowy czterogwiazdkowy hotel zaledwie 8 minut od centrum Warszawy. "
            "Trzy sale weselne o różnym charakterze: klasyczna, nowoczesna i kameralna. "
            "Wykwintna kuchnia i profesjonalny koordynator weselny."
        ),
        "address": "al. Krakowska 218, 02-219 Warszawa",
        "city": "Warszawa",
        "phone": "+48 22 573 12 00",
        "email": "wesela@hotellord.pl",
        "website": "https://hotellord.pl",
        "max_guests": 470,
        "price_per_person": Decimal("345.00"),
        "has_parking": True,
        "has_garden": True,
        "has_dance_floor": True,
        "has_accommodation": True,
        "latitude": Decimal("52.1810"),
        "longitude": Decimal("20.9530"),
        "show_calendar": True,
        "hours": ("09:00", "02:00"),
        "image_url": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800",
    },
    {
        "name": "Dwór Złotopolska Dolina",
        "description": (
            "Wyjątkowy obiekt na skraju malowniczych Złotopolic pod Nowym Dworem "
            "Mazowieckim. Elegancki dwór w otoczeniu zieleni, sala na 200 osób, "
            "noclegi i plenerowe ceremonie ślubne."
        ),
        "address": "ul. Modlińska 114, 05-100 Nowy Dwór Mazowiecki",
        "city": "Warszawa",
        "phone": "+48 22 713 15 55",
        "email": "info@zlotopolskadolina.pl",
        "website": "https://zlotopolskadolina.pl",
        "max_guests": 200,
        "price_per_person": Decimal("280.00"),
        "has_parking": True,
        "has_garden": True,
        "has_dance_floor": True,
        "has_accommodation": True,
        "latitude": Decimal("52.4310"),
        "longitude": Decimal("20.7160"),
        "show_calendar": False,
        "hours": ("10:00", "00:00"),
        "image_url": "https://images.unsplash.com/photo-1568084680786-a84f91d1153c?w=800",
    },
    {
        "name": "Zamek Rokosowo",
        "description": (
            "Zabytkowy zamek wielkopolski położony między Lesznem i Krotoszynem. "
            "Doskonałe sale weselne w barokowych wnętrzach, piękny park, "
            "noclegi dla 145 gości i niezapomniana atmosfera minionych epok."
        ),
        "address": "Rokosowo 1, 63-805 Łęka Mała",
        "city": "Poznań",
        "phone": "+48 65 571 94 02",
        "email": "zamek@rokosowo.pl",
        "website": "https://zamekrokosowo.pl",
        "max_guests": 200,
        "price_per_person": Decimal("260.00"),
        "has_parking": True,
        "has_garden": True,
        "has_dance_floor": True,
        "has_accommodation": True,
        "latitude": Decimal("51.8200"),
        "longitude": Decimal("17.2350"),
        "show_calendar": True,
        "hours": ("10:00", "23:00"),
        "image_url": "https://images.unsplash.com/photo-1533104816931-20fa691ff6ca?w=800",
    },
]

# ── 3. Menu weselne dla każdej restauracji ──────────────────────────────

MENUS = {
    "Pałac Wąsowo": [
        ("appetizer", "Tatar wołowy z kaparami",          "Świeży tatar z polędwicy, kaparsy, cebula, żółtko",            38),
        ("appetizer", "Carpaccio z buraka",                "Z kozim serem i orzechami włoskimi",                           32),
        ("appetizer", "Krewetki w tempurze",               "Z sosem sweet chili i miksem sałat",                           42),
        ("soup",      "Krem z białych szparagów",          "Z truflowym olejem i grzankami",                               28),
        ("soup",      "Rosół z kury domowej",              "Z domowym makaronem, tradycyjny przepis",                      22),
        ("main",      "Polędwica wołowa Wellington",       "Z foie gras, w cieście francuskim z sosem z Porto",           85),
        ("main",      "Łosoś pieczony na cedrze",          "Z purée z selera i szpinakiem",                               68),
        ("main",      "Kaczka konfitowana",                "Z glazurą z żurawiny, ziemniaki gratin",                      72),
        ("main",      "Risotto z borowikami",              "Kremowe risotto z leśnymi grzybami i parmezanem",             58),
        ("dessert",   "Fondant czekoladowy",               "Z lodami waniliowymi i malinami",                             32),
        ("dessert",   "Panna cotta z mango",               "Z coulis z marakui",                                          28),
        ("buffet",    "Stół szwedzki zimny",               "Szynka parmeńska, sery, owoce morza, sałatki",               65),
        ("drink",     "Kompot z jabłek i cynamonu",        "",                                                            12),
        ("drink",     "Wino Prosecco (kieliszek)",         "Włoskie musujące wino na toast",                              28),
    ],
    "Dworek Separowo": [
        ("appetizer", "Bruschetta z pomidorami",           "Na pieczywie razowym z bazylią",                               24),
        ("appetizer", "Roladki z łososia wędzonego",       "Z serkiem kremowym i kaparami",                                36),
        ("soup",      "Żurek staropolski",                 "Z białą kiełbasą i jajkiem",                                  24),
        ("soup",      "Krem z dyni",                       "Z prażonymi pestkami i oliwą truflową",                        26),
        ("main",      "Schab pieczony",                    "Z jabłkami i żurawiną, pyzy ziemniaczane",                     52),
        ("main",      "Filet z sandacza",                  "W maśle szałwiowym z warzywami sezonowymi",                   64),
        ("main",      "Pierś z kaczki",                    "Z sosem pomarańczowym i kluskami śląskimi",                   62),
        ("dessert",   "Sernik nowojorski",                 "Z sosem z owoców leśnych",                                    26),
        ("dessert",   "Szarlotka na ciepło",               "Z lodami waniliowymi i karmelem",                             24),
        ("buffet",    "Bufet sałatkowy",                   "10 rodzajów sałatek sezonowych",                              35),
        ("drink",     "Lemoniada domowa",                  "Cytryna, mięta, ogórek",                                      14),
        ("drink",     "Piwo kraftowe lokalne",             "Browaru Fortuna 0.5L",                                        16),
    ],
    "Hotel Remes Sport & Spa": [
        ("appetizer", "Foie gras z konfiturą figową",      "Na brioszce z mikro-zieleniną",                               58),
        ("appetizer", "Tartar z tuńczyka",                 "Z awokado i sosem sojowym, na chipsie ryżowym",               48),
        ("appetizer", "Burrata z pomidorami",              "Ser burrata, pomidory malinowe, bazylia, oliwa",              42),
        ("soup",      "Bisque z homara",                   "Z tostami i aioli",                                           38),
        ("soup",      "Zupa cebulowa",                     "Zapiekana z gruyère i grzankami",                             28),
        ("main",      "Stek z polędwicy",                  "Wagyu, grillowane warzywa, sos béarnaise",                    120),
        ("main",      "Turbot pieczony",                   "Z purée z topinamburu i sosem szampańskim",                    95),
        ("main",      "Comber jagnięcy",                   "W ziołowej panierce z ratatouille",                            88),
        ("main",      "Ravioli z ricottą",                 "W sosie maślano-szałwiowym z parmezanem",                      62),
        ("dessert",   "Crème brûlée",                      "Klasyczna z laską wanilii",                                   32),
        ("dessert",   "Tarta z owocami sezonowymi",        "Na kruchym cieście z kremem patissière",                      34),
        ("dessert",   "Lody domowe (3 gałki)",             "Pistacja, wanilia, czekolada",                                28),
        ("buffet",    "Stacja serów polskich",             "12 gatunków serów z miodem i orzechami",                      55),
        ("drink",     "Wino białe Sauvignon Blanc",        "Kieliszek 150ml, Nowa Zelandia",                              32),
        ("drink",     "Koktajl Aperol Spritz",             "Aperol, prosecco, woda gazowana",                             28),
    ],
    "Stary Kamionek": [
        ("appetizer", "Smalec domowy z ogórkiem",          "Na chlebie wiejskim, z cebulką i skwarkami",                  18),
        ("appetizer", "Tatar ze śledzia",                  "Z jabłkiem, cebulą i śmietaną",                               22),
        ("soup",      "Barszcz czerwony z uszkami",        "Tradycyjny, z grzybowymi uszkami",                            22),
        ("soup",      "Zupa grzybowa z łazankami",         "Z suszonych borowików",                                       24),
        ("main",      "Golonka pieczona",                  "Z kapustą zasmażaną i chrzanem",                              48),
        ("main",      "Kotlet schabowy",                   "Z ziemniakami i surówką z kapusty",                           44),
        ("main",      "Pierogi ruskie",                    "Z masłem i cebulką, 12 szt.",                                 36),
        ("main",      "Żeberka BBQ",                       "W domowym sosie BBQ z coleslaw",                              52),
        ("dessert",   "Makowiec domowy",                   "Z polewą czekoladową",                                        18),
        ("dessert",   "Naleśniki z serem",                 "Ze śmietaną i dżemem truskawkowym",                           22),
        ("buffet",    "Stół wędlin domowych",              "Szynka, kiełbasy, pasztety, chleb",                           45),
        ("drink",     "Kompot z owoców",                   "Truskawka, malina, jabłko",                                   10),
        ("drink",     "Nalewka domowa (50ml)",             "Wiśniowa lub pigwowa",                                        18),
    ],
    "Rio Grande Moments": [
        ("appetizer", "Ceviche z labraksa",                "Z awokado, kolendrą i limonką",                               44),
        ("appetizer", "Tataki z tuńczyka",                 "Z sezamem i sosem ponzu",                                     48),
        ("soup",      "Tom Kha Gai",                       "Tajska kokosowa z kurczakiem",                                 32),
        ("soup",      "Gazpacho andaluzyjskie",            "Chłodnik pomidorowy z bazylią",                               26),
        ("main",      "Stek Ribeye 300g",                  "Z masłem czosnkowym i frytkami truflowymi",                   88),
        ("main",      "Krewetki tygrysie",                 "Na grillu z risotto cytrynowym",                              78),
        ("main",      "Kurczak tandoori",                  "Z ryżem basmati i naan chlebem",                              56),
        ("main",      "Bowl wegetariański",                "Quinoa, awokado, bataty, hummus, warzywa",                    48),
        ("dessert",   "Brownie z lodami",                  "Ciepłe brownie z lodami pistacjowymi",                        32),
        ("dessert",   "Tiramisu klasyczne",                "Z mascarpone i espresso",                                     30),
        ("buffet",    "Stacja grill",                      "Kiełbaski, steki, warzywa z grilla, sosy",                    75),
        ("drink",     "Mojito bezalkoholowe",              "Limonka, mięta, cukier trzcinowy, soda",                      18),
        ("drink",     "Wino czerwone Malbec",              "Kieliszek 150ml, Argentyna",                                  34),
    ],
    "Pałacyk Pod Lipami": [
        ("appetizer", "Pasta z łososia",                   "Z chlebem tostowym i rukolą",                                 28),
        ("appetizer", "Jajka po benedyktyńsku",            "Z szynką, sosem holenderskim",                                34),
        ("soup",      "Krem z pomidorów",                  "Z bazylią i grzankami",                                       20),
        ("soup",      "Rosół królewski",                   "Z drobnym makaronem i marchewką",                             22),
        ("main",      "Filet z dorsza",                    "W panierce z ziołami, z puree i szpinakiem",                  58),
        ("main",      "Kotlet de volaille",                "Z masłem ziołowym, frytki, surówka",                          46),
        ("main",      "Gnocchi z pesto",                   "Z pomidorkami cherry i parmezanem",                            42),
        ("dessert",   "Suflet czekoladowy",                "Z lodami malinowymi",                                         28),
        ("dessert",   "Jabłecznik z cynamonem",            "Z bitą śmietaną",                                             22),
        ("drink",     "Herbata owocowa",                   "Hibiskus, dzika róża, malina",                                12),
        ("drink",     "Kawa latte",                        "Z mlekiem owsianym na życzenie",                              16),
    ],
    "Hotel Poznański": [
        ("appetizer", "Deska serów i wędlin",              "Selekcja polskich delikatesów",                               44),
        ("appetizer", "Krewetki marynowane",               "Z czosnkiem, chili i kolendrą",                               38),
        ("soup",      "Żurek w chlebie",                   "Na kwasie, z kiełbasą i jajkiem",                             26),
        ("soup",      "Krem z brokułów",                   "Z prażonymi migdałami",                                       22),
        ("main",      "Polędwiczki wieprzowe",             "W sosie z zielonego pieprzu, z gratin",                       56),
        ("main",      "Łosoś sous vide",                   "Z warzywami na parze i sosem cytrynowym",                     68),
        ("main",      "Kluseczki ze szpinakiem",           "W sosie serowym z gorgonzolą",                                42),
        ("main",      "Pieczeń wołowa",                    "Z sosem chrzanowym, kluski śląskie, kapusta",                 58),
        ("dessert",   "Lava cake",                         "Ciepły czekoladowy z lodami waniliowymi",                     30),
        ("dessert",   "Pączki z różą",                     "2 szt., z cukrem pudrem",                                     16),
        ("buffet",    "Stacja bar sałatkowy",              "8 rodzajów sałatek z dressingami",                            30),
        ("drink",     "Sok świeżo wyciskany",              "Pomarańcza, jabłko-marchew lub grejpfrut",                    14),
        ("drink",     "Piwo Lech Premium 0.5L",            "",                                                            14),
    ],
    "Hotel Lord Warszawa": [
        ("appetizer", "Sashimi z łososia i tuńczyka",      "Z imbirem, wasabi i sosem sojowym",                           56),
        ("appetizer", "Vitello tonnato",                    "Cielęcina z sosem tuńczykowym i kaparami",                    48),
        ("appetizer", "Gęsie rillettes",                   "Z konfiturą z cebuli i chlebem grillowanym",                  42),
        ("soup",      "Consommé wołowe",                   "Klarowny bulion z raviolkami ze szpinaku",                    34),
        ("soup",      "Krem z karczocha",                  "Z oliwą truflową i chipsem z szynki parmeńskiej",             36),
        ("main",      "Filet mignon",                      "Z puree z pora, sos demi-glace z madeirą",                    98),
        ("main",      "Halibut atlantycki",                "Na risotto szafranowym ze szparagami",                         92),
        ("main",      "Rack jagnięcy",                     "Z ziołową krustą, warzywa glazurowane",                        95),
        ("main",      "Pierś z perliczki",                 "Z musem z pieczonej papryki i polentą",                       78),
        ("dessert",   "Trufle czekoladowe (6 szt.)",       "Belgijska czekolada, kakao, orzechy",                         38),
        ("dessert",   "Deser mille-feuille",               "Ciasto francuskie z kremem waniliowym",                       36),
        ("dessert",   "Sorbet cytrynowy z limoncello",     "Odświeżający, z miętą",                                      28),
        ("buffet",    "Stół z owocami morza",              "Ostrygi, krewetki, małże, kraby",                             120),
        ("drink",     "Szampan Moët & Chandon",            "Kieliszek 150ml",                                            58),
        ("drink",     "Koktajl Espresso Martini",          "Wódka, kahlúa, espresso",                                    36),
    ],
    "Dwór Złotopolska Dolina": [
        ("appetizer", "Galareta z prosięcia",              "Z chrzanem i musztardą",                                      26),
        ("appetizer", "Tatar z jelenia",                   "Z brusznicami i pieczywem",                                   44),
        ("soup",      "Barszcz ukraiński",                 "Z wołowiną, burakami i śmietaną",                             24),
        ("soup",      "Krupnik polski",                    "Na żeberkach z kaszą jęczmienną",                             22),
        ("main",      "Dzik pieczony",                     "Z sosem z czarnych oliwek, knedle",                           68),
        ("main",      "Pstrąg po myśliwsku",               "Z boczkiem, migdałami i masłem",                              58),
        ("main",      "Rolada z kaczki",                   "Z suszonymi śliwkami, ziemniaki opiekane",                    62),
        ("main",      "Pierogi z dziczyzną",               "Z sosem grzybowym, 10 szt.",                                  42),
        ("dessert",   "Tort orzechowy",                    "Z kremem kawowym i polewą czekoladową",                       28),
        ("dessert",   "Racuchy z jabłkami",                "Z cukrem pudrem i sosem waniliowym",                          22),
        ("buffet",    "Stół z dziczyzną",                  "Pasztety, kiełbasy myśliwskie, pieczywa",                     55),
        ("drink",     "Grzane wino",                       "Aromatyczne z cynamonem i pomarańczą",                        18),
        ("drink",     "Nalewka myśliwska (50ml)",          "Na dzikiej róży i jałowcu",                                   22),
    ],
    "Zamek Rokosowo": [
        ("appetizer", "Carpaccio z polędwicy",             "Z kaparami, rukolą i parmezanem",                             38),
        ("appetizer", "Sakiewki z ciasta filo",            "Z serem brie i żurawiną",                                     32),
        ("soup",      "Zupa rybna bouillabaisse",          "Z grzankami czosnkowymi i rouille",                           34),
        ("soup",      "Krem z białej fasoli",              "Z rozmarynem i truflą",                                       26),
        ("main",      "Medaliony z polędwicy",             "Z sosem z moreli i koniaku, puree ziemniaczane",              76),
        ("main",      "Dorsz w sosie śmietanowym",         "Z kaparami i koprem, ryż jaśminowy",                          62),
        ("main",      "Kurczak faszerowany",               "Szpinakiem i fetą, warzywa pieczone",                         54),
        ("main",      "Tagliatelle z boczniakami",         "W kremowym sosie z tymiankiem",                               48),
        ("dessert",   "Profiteroles z czekoladą",          "Ptysiowe z lodami i polewą czekoladową",                      30),
        ("dessert",   "Tort bezowy Pavlova",               "Z bitą śmietaną i owocami leśnymi",                          28),
        ("buffet",    "Bufet deserowy",                    "Ciasta, torty, owoce, czekoladowa fontanna",                  60),
        ("drink",     "Wino musujące Cava",                "Kieliszek 150ml, Hiszpania",                                  26),
        ("drink",     "Herbata Earl Grey",                 "Z cytryną i miodem",                                          14),
    ],
}

# ── 4. Opinie testowe ────────────────────────────────────────────────────
REVIEW_COMMENTS = [
    ("Fantastyczne wesele! Obsługa na najwyższym poziomie.", 5),
    ("Piękna sala, smaczne jedzenie. Polecam każdemu!", 5),
    ("Bardzo ładne miejsce, ale obsługa mogłaby być szybsza.", 4),
    ("Świetna lokalizacja i klimat. Wrócę tu na pewno.", 5),
    ("Dobre jedzenie, ale trochę za drogo jak na możliwości.", 3),
    ("Rewelacyjne wesele, goście byli zachwyceni!", 5),
    ("Solidnie, profesjonalnie, bez zarzutu.", 4),
    ("Piękne wnętrza, romantyczna atmosfera.", 5),
    ("Porcje mogłyby być większe, ale smak doskonały.", 4),
    ("Idealne miejsce na kameralne przyjęcie.", 4),
]

# Konta recenzentów (tworzymy ich jeśli nie ma)
REVIEWERS = [
    ("anna_k", "Anna", "Kowalska"),
    ("marek_n", "Marek", "Nowak"),
    ("kasia_w", "Katarzyna", "Wiśniewska"),
    ("piotr_z", "Piotr", "Zieliński"),
    ("ewa_m", "Ewa", "Mazur"),
]

reviewer_users = []
for uname, fname, lname in REVIEWERS:
    u, _ = User.objects.get_or_create(
        username=uname,
        defaults={"first_name": fname, "last_name": lname, "email": f"{uname}@test.pl"},
    )
    if _:
        u.set_password("Test1234!")
        u.save()
    reviewer_users.append(u)

# ── 5. Tworzenie restauracji, menu i opinii ──────────────────────────────
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

for i, data in enumerate(RESTAURANTS, 1):
    name = data["name"]
    # Pomijaj jeśli już istnieje
    if Restaurant.objects.filter(name=name).exists():
        print(f"⏭️  {name} już istnieje, pomijam")
        continue

    hours_open, hours_close = data.pop("hours")
    open_t = time(*map(int, hours_open.split(":")))
    close_t = time(*map(int, hours_close.split(":")))

    # Losowe warianty godzin: zamknięte w pn (30%), krótsze w nd (50%)
    hour_fields = {}
    for d in DAYS:
        if d == "mon" and random.random() < 0.3:
            hour_fields[f"{d}_open"] = None
            hour_fields[f"{d}_close"] = None
        elif d == "sun" and random.random() < 0.5:
            hour_fields[f"{d}_open"] = time(12, 0)
            hour_fields[f"{d}_close"] = time(20, 0)
        else:
            hour_fields[f"{d}_open"] = open_t
            hour_fields[f"{d}_close"] = close_t

    r = Restaurant.objects.create(
        firm_type=Restaurant.FirmType.VENUE,
        name=data["name"],
        description=data["description"],
        address=data["address"],
        city=data["city"],
        phone=data["phone"],
        email=data["email"],
        website=data["website"],
        image_url=data["image_url"],
        max_guests=data["max_guests"],
        price_per_person=data["price_per_person"],
        has_parking=data["has_parking"],
        has_garden=data["has_garden"],
        has_dance_floor=data["has_dance_floor"],
        has_accommodation=data["has_accommodation"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        show_calendar=data["show_calendar"],
        **hour_fields,
    )

    # Powiąż z FatBob jako owner
    RestaurantOwner.objects.get_or_create(
        user=user,
        restaurant=r,
        defaults={"role": RestaurantOwner.Role.OWNER},
    )

    # Utwórz menu
    menu = Menu.objects.create(
        restaurant=r, name="Menu weselne", is_active=True, last_edited_by=user,
    )

    items = MENUS.get(name, [])
    for order, (cat, item_name, desc, price) in enumerate(items, 1):
        MenuItem.objects.create(
            restaurant=r,
            menu=menu,
            category=cat,
            name=item_name,
            description=desc,
            price=Decimal(str(price)),
            order=order,
        )

    # Losowe opinie (2-4 na restaurację)
    num_reviews = random.randint(2, 4)
    chosen = random.sample(list(zip(reviewer_users, REVIEW_COMMENTS)), num_reviews)
    for reviewer, (comment, rating) in chosen:
        # Losowa modyfikacja ratingu ±1
        actual_rating = max(1, min(5, rating + random.choice([-1, 0, 0, 0, 1])))
        Review.objects.get_or_create(
            user=reviewer,
            restaurant=r,
            defaults={"rating": actual_rating, "comment": comment},
        )

    print(f"✅ [{i}/10] {name} — {len(items)} pozycji menu, {num_reviews} opinii")

print("\n🎉 Gotowe! 10 restauracji FatBoba załadowanych.")
