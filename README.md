# Vytváranie faktúr
Skripty pre rýchle vytváranie faktúr na STROMácke akcie.

## Návod pre vyplnenie súborov na akciu
1. Nájdi v priečinku `templates` súbory k typu akcie, na ktorú chceš faktúry vytvoriť.
2. Vyplň údaje v `.csv` všetky údaje. Ak fakturujeme na osobu, stačí vyplniť to čo uviedli. Ak fakturujeme na firmu treba uviesť všetko aj IČO. Postupuj ako v návode nižšie.
3. Vyplň nastavenia v `.yaml` súbore. Podľa návodu nižšie.
4. Pošli oba súbory na mail osobe, ktorá má povolenie spravovať faktúry.

### Vyplnenie údajov o odberateľoch (`.csv` súbor)

Popis možných stĺpcov:
 - `o_name` - Meno firmy, školy alebo rodiča, prípadne účastníka (ak už mal 18).
 - `o_street` - Ulica s číslom sídla firmy/bydlisko
 - `o_city` - Mesto sídla
 - `o_state` - Štát sídla. Zvyčajne Slovensko.
 - `o_zip` - PSČ
 - `o_ico` - IČO v prípade firmy. Ak sa jedná o rodiča/ účastníka ostáva prázdne.
 - `o_dic` - DIČ v prípade firmy. Ak sa jedná o rodiča/ účastníka ostáva prázdne.
 - `o_icdph` - 
 - `o_email` - Email (nepovinné)
 - `ucastnicky` - pocet kusov, kolkokrat danu vec uhradzaju (1)
 - `f_paid` - Suma, ktorá už bola uhradená
 - `i_date_paid` - Dátum úhrady. Je potrebné vyplniť iba ak bolo niečo vyplnené v `f_paid`.
 - `f_payment` - Možné hodnoty: `hotovost`,`prevod`,`karta`. Ak nie je uvedené, defaultne sa použije `prevod`

Ďalej je možné doplniť vlastné stĺpce a to konkrétne dva typy.
1. Prvý typ má `i_*` musíme mať teda prefix `i_`. Napríklad `i_meno_ucastnika`. Takýto stĺpec.
2. Druhý typ sú položky. Napríklad účastnícky poplatok alebo bageta. Názov stĺpca musí zodpovedať položke v nastaveniach pod kľúčom `polozky`. Tieto názvy nesmú mať prefixy `i_`, `o_`, `f_`.

Ďalej je možné aplikovať ďalšie polia podľa návodu [https://www.faktury-online.com/faktury-online-api/manual](https://www.faktury-online.com/faktury-online-api/manual)

### Vyplnenie nastavení (`.yaml` súbor)

## Návod pre prácu so scriptami

### Setup

Pre spustenie treba najprv nainštalovať dependencie:
```
pip install -r requirements.txt
```
Pre zakladanie faktúr je potrebné taktiež pridať file s názvom `api_key.txt` do priečinka `.secrets`. Do tohto súboru skopíruj API kľúč z nášho konta na faktury-online.com

### Spustenie
Pre vytvorenie faktúry použi príkaz
```
python faktury.py skontroluj sustredenie
```

```
python faktury.py vytvor sustredenie
```

Generovanie výstupu do denníka
```
python faktury.py dennik 2023-01-01 2023-01-31
```