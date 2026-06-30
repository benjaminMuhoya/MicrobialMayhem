# Welcome to Microbial Mayhem!

Where battling bacteria teach you some biology.

This is the beta version! Thank you for being our tester :)

## Install
```
pip3 install PyObjC
conda install playsound
pip install pygame
```

## Clone repository
```
git clone git@github.com:htoth99/MicrobialMayhem.git
cd MicrobialMayhem

## Alternative with HTTPS

git clone https://github.com/htoth99/MicrobialMayhem.git
cd MicrobialMayhem
```

## To play the game, simply type:

```
./microbial_mayhem_main.py #on your command line prompt, press "return"
and follow the prompts to choose your strain and its attributes!
```


May the best bug win!

## Rebuild the fighter catalog

The game reads the normalized runtime database at
`data/catalog/microbial_mayhem_catalog.sqlite3`.

To migrate an existing generated JSON catalog:

```bash
python3 scripts/migrate_catalog_to_sqlite.py
```

To rebuild from a retained BacDive export with local MIBiG enrichment:

```bash
python3 scripts/build_bacdive_catalog.py \
  --bacdive-json data/bacdive/bacdive_records.json
```

The large BacDive export, legacy generated JSON catalog, and raw API cache are
local rebuild inputs and are intentionally ignored by Git.
