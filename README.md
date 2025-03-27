## Finální verze maturitní práce
Filip Viliam Džupin

## Autorská práva
Tato aplikace byla vytvořena výhradně pro vzdělávací účely v rámci mé maturitní práce a není určena ke komerčnímu využití. Primárním cílem bylo prozkoumat možnosti implementace umělé inteligence v rámci deskových her a využití OpenAI API pro imitaci lidských rozhodnutí. 
Použité obrázky karet pocházejí ze skutečných karet obsažených ve verzi Dixit Odyssey, jejichž autorská práva náleží společnosti Libellud a jednotlivým ilustrátorům. Tyto obrázky slouží pouze jako demonstrace funkcionality aplikace.


## Uživatelská Dokumentace

Aplikace je nástrojem, který vizualizuje simulaci karetní hry Dixit, uživatel se tedy nezapojuje do herního dění a je pozorovatelem.

### Instalace a spuštění

Pro správné fungování aplikace je potřeba mít nainstalovaný nejen soubor se samotnou aplikací, ale i knihovny určené v souboru `requirements.txt`. Pokud je toto dodrženo, je dále potřeba už jen uložit svůj API klíč do souboru `sk.py`, ze kterého se naimportuje do hry. Soubory `dixit.log` a `images.json` se vytvoří automaticky. Konkrétní požadavky byly popsány v kapitole 2.1.

Aplikace se dá spustit vícero způsoby. První způsob je spuštění přímo pomocí příkazového řádku, nebo spuštěním dávkového souboru `run_game.bat` či `run_game.sh`, který spustí program `main.py`. Druhý způsob je spuštění souboru `main.py` skrze nějaké IDE (tj. vývojové prostředí; PyCharm, Visual Studio Code, …). Protože takto lze jednoduše upravit chování jednotlivých hráčů skrze upravení instancí přímo v kódu, je tento způsob doporučený.

### Ovládání aplikace

Po zapnutí aplikace se zobrazí úvodní obrazovka, na které se nachází dvě tlačítka. První z nich je tlačítko „Začít hru“, jeho funkcí je započnutí hry. Druhé je tlačítko „Log“, které otevře okno s žurnálem.

Po zapnutí hry se zobrazí náhledová obrazovka s hráči a jejich kartami. Uprostřed obrazovky je text, který oznamuje aktuální dění a jméno hráče, který je pro toto kolo vypravěčem. Dále jsou v každém rohu panely hráčů, kteří v této hře hrají. Zde jsou zobrazeny jejich karty, jména a aktuální skóre. Tlačítka ve spodní liště jsou vypnuta.

Po vypočtení tahu se jeho výsledky automaticky promítnou na plátno. Ke jménu hráče, který je vypravěč, se přidá popis karty, kterou vybral. Každý hráč má před jménem kolečko dané barvy, která mu byla přiřazena. Touto barvou se orámečkuje i karta, kterou vybral, aby bylo jasné, že patří jemu. Uprostřed plátna je vizualizace karet na stole s příslušnými barvami a jmény. Jména pod kartami značí, jaký hráč pro danou kartu hlasoval.

Ve spodní liště nalevo nalezneme tlačítko „Log“ a text s informací, v jakém kole se hráči nachází a kdo je vypravěčem. Vpravo dole je tlačítko „Zahraj další tah“, který posune hru dál. Po zmáčknutí tlačítka se znovu spustí náhled a čeká se na vypočtení tahu. Tento proces se opakuje až do konce hry, tedy když některý z hráčů získá 30 bodů a více.

Tlačítko „Log“ zobrazuje výpis všech akcí, které během hry proběhly. Každý log se skládá z časové stopy a přesným výpisem co akce znamenala.

V přiloženém obrázku se informace zobrazují v debug módu, který mimo jiné urychluje průběh hry, a tak tedy jsou časové stopy zaznamenány blíže k sobě.

Pokud je tlačítko „Zahraj další tah“ stlačeno ve chvíli, kdy některý z hráčů získal 30 a více bodů, tak se místo vypočítávání dalšího kola a zobrazení náhledu hra ukončí a vytvoří se obrazovka, na které je napsáno jméno vítěze a jeho finální počet bodů. V tento moment už není možné pustit další tah. Zobrazení logu je stále možné.

### Nastavení herních podmínek a jejich úprava

Nastavení povah, jmen hráčů a koeficientů náhodnosti (temperature) je možné při inicializaci instancí hráčů. Toto je možné přímo v souboru, ze které je aplikace spouštěna.

Upravení promptu pro jazykové modely je možné pouze v souboru `dixit_game.py`, kde je třída hráče definována.
