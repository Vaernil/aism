# Projekt na aism - agregator treści w Django
To repo ma służyć głównie mojej nauce, dlatego zawiera dużo niepotrzebnych
komentarzy, a niektóre rzeczy nie działają.
## Funkcje
* dodawanie treści i komentarzy
* użytkownik może głosować tylko raz na dany komentarz czy dyskusję
* sortowanie wg. daty dodania
* i inne

## TODO
* add Polish pluralization for words
* Stick to one language in project comments, I think Egnlish being lingua franca is the way to go
* Fully translate this readme to English
* Translate everything to 2 languages English and Polish and add a function that lets you switch between the two
* Add dark and white theme
* Add searching
* Add displaying only questions
* Add downvote button
* Change vote button color whether it was pressed or not
* move hardcodes css to stylesheet
* Deploy
* play with manage.py script
* can you even have bilingual readme and is there any point to keeping Polish?

## Do poczytania | Stuff to read
https://wiki.archlinux.org/index.php/Python/Virtual_environment

0.0.0.0 vs 127.0.0.1 vs localhost
https://stackoverflow.com/questions/20778771/what-is-the-difference-between-0-0-0-0-127-0-0-1-and-localhost


## Inicjalizacja projektu (Linux)

* Sklonuj repo:  
```bash
git clone git@github.com:Vaernil/aism.git
```

* Zainstaluj virtualenv

Gentoo
```bash
sudo emerge virtualenv
```
Ubuntu
```bash
sudo apt install virtualenv python3-dev
```

* Stwórz wirtualne środowisko
```bash
cd ./aism
virtualenv -p python3 env
source env/bin/activate
pip install -r requirements.txt
```

* Usuń poprzednią bazę danych i rozpocznij na czysto
```bash
bash restart_db
```

* Albo wystartuj
```bash
bash start_dev
```
* Otwórz url: http://0.0.0.0:8000
* Stron administracyjna: http://0.0.0.0:8000/admin

* Jeśli chcesz zakończyć virtualenv
```bash
deactivate
```
