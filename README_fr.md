# ![oneDriveOOo logo][1] oneDriveOOo
<!--
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020 https://prrvchr.github.io                                     ║
║                                                                                    ║
║   Permission is hereby granted, free of charge, to any person obtaining            ║
║   a copy of this software and associated documentation files (the "Software"),     ║
║   to deal in the Software without restriction, including without limitation        ║
║   the rights to use, copy, modify, merge, publish, distribute, sublicense,         ║
║   and/or sell copies of the Software, and to permit persons to whom the Software   ║
║   is furnished to do so, subject to the following conditions:                      ║
║                                                                                    ║
║   The above copyright notice and this permission notice shall be included in       ║
║   all copies or substantial portions of the Software.                              ║
║                                                                                    ║
║   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                  ║
║   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                  ║
║   OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.        ║
║   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY             ║
║   CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,             ║
║   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE       ║
║   OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                    ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
-->

**This [document][2] in English.**

**L'utilisation de ce logiciel vous soumet à nos [Conditions d'utilisation][3] et à notre [Politique de protection des données][4].**

# version [0.0.6][5]

## Introduction:

**oneDriveOOo** fait partie d'une [Suite][6] d'extensions [LibreOffice][7] et/ou [OpenOffice][8] permettant de vous offrir des services inovants dans ces suites bureautique.  
Cette extension vous permet de travailler dans LibreOffice / OpenOffice sur vos fichiers Microsoft OneDrive, même hors ligne.

Etant un logiciel libre je vous encourage:
- A dupliquer son [code source][9].
- A apporter des modifications, des corrections, des ameliorations.
- D'ouvrir un [dysfonctionnement][10] si nécessaire.

Bref, à participer au developpement de cette extension.
Car c'est ensemble que nous pouvons rendre le Logiciel Libre plus intelligent.

## Prérequis:

oneDriveOOo utilise une base de données locale [HsqlDB][11] version 2.7.1.  
HsqlDB étant une base de données écrite en Java, son utilisation nécessite [l'installation et la configuration][12] dans LibreOffice / OpenOffice d'un **JRE version 11 ou ultérieure**.  
Je vous recommande [Adoptium][13] comme source d'installation de Java.

Si vous utilisez **LibreOffice sous Linux**, vous devez vous assurez de deux choses:
  - Vous êtes sujet au [dysfonctionnement 139538][14]. Pour contourner le problème, veuillez **désinstaller les paquets** avec les commandes:
    - `sudo apt remove libreoffice-sdbc-hsqldb`
    - `sudo apt remove libhsqldb1.8.0-java`

Si vous souhaitez quand même utiliser la fonctionnalité HsqlDB intégré fournie par LibreOffice, alors installez l'extension [HsqlDBembeddedOOo][15].  

  - Si le paquet python3-cffi-backend est installé alors vous devez **installer le paquet python3-cffi** avec la commande:
    - `dpkg -s python3-cffi-backend` (pour savoir si le paquet est installé)
    - `sudo apt install python3-cffi`

OpenOffice et LibreOffice sous Windows ne sont pas soumis à ces dysfonctionnements.

## Installation:

Il semble important que le fichier n'ait pas été renommé lors de son téléchargement.  
Si nécessaire, renommez-le avant de l'installer.

- Installer l'extension ![OAuth2OOo logo][16] **[OAuth2OOo.oxt][17]** version 0.0.6.

Vous devez d'abord installer cette extension, si elle n'est pas déjà installée.

- Installer l'extension ![jdbcDriverOOo logo][18] **[jdbcDriverOOo.oxt][19]** version 0.0.4.

Vous devez installer cette extension, si elle n'est pas déjà installée.

- Installer l'extension ![oneDriveOOo logo][1] **[oneDriveOOo.oxt][20]** version 0.0.6.

Redémarrez LibreOffice / OpenOffice après l'installation.

## Configuration:

Configurer les boîtes de dialogue Ouvrir / Enregistrer de LibreOffice (non nécessaire sous OpenOffice):

- **Pour LibreOffice V5.x et avant:**

Dans le menu: Outils - Options - LibreOffice - General: cocher utiliser les boîtes de dialogue LibreOffice.

- **Pour LibreOffice V6.x et aprés:**

Dans le menu: Outils - Options - LibreOffice - Advancé - Ouvrir la configuration avancée

Rechercher: UseSystemFileDialog (Trouvé sous: org.openoffice.Office.Common > Misc)

Editer ou changer "true" par "false" (réglez-le sur "false")

## Utilisation:

Si vous êtes sous LibreOffice, il est important d'avoir au préalable [reconfiguré les boîtes de dialogue][21] Ouvrir / Enregistrer.

**Ouvrir votre OneDrive Microsoft:**

Dans: **Fichier -> Ouvrir** saisir dans la première liste déroulante:

- Pour une Url nommée: **vnd-microsoft://votre_adresse@votre_fournisseur**  

ou

- Pour une url non nommée (anonyme): **vnd-microsoft:///**

Si vous ne donnez pas **votre_adresse@votre_fournisseur**, elle vous sera demandée...

Les Urls anonymes vous permettent de rester anonyme (votre compte n'apparaît pas dans l'Url) tandis que les Urls nommées vous permettent d'accéder à plusieurs comptes simultanément.

Après avoir autorisé l'application [OAuth2OOo][22] à accéder à vos fichiers de votre Microsoft OneDrive, vos fichiers OneDrive devraient apparaître!!! normalement  ;-)

## A été testé avec:

* LibreOffice 6.4.4.2 - Ubuntu 20.04 -  LxQt 0.14.1

* LibreOffice 7.0.0.0.alpha1 - Ubuntu 20.04 -  LxQt 0.14.1

* OpenOffice 4.1.8 x86_64 - Ubuntu 20.04 - LxQt 0.14.1

* OpenOffice 4.2.0.Build:9820 x86_64 - Ubuntu 20.04 - LxQt 0.14.1

* LibreOffice 6.1.5.2 - Raspbian 10 buster - Raspberry Pi 4 Model B

* LibreOffice 6.4.4.2 (x64) - Windows 7 SP1

Je vous encourage en cas de problème :-(  
de créer un [dysfonctionnement][10]  
J'essaierai de le résoudre ;-)

## Historique:

### Ce qui a été fait pour la version 0.0.5:

- Intégration et utilisation de la nouvelle version de Hsqldb 2.5.1.

- Ecriture d'une nouvelle interface [Replicator][23], lancé en arrière-plan (python Thread) responsable de:

    - Effectuer les procédures nécessaires lors de la création d'un nouvel utilisateur (Pull initial).

    - Effectuer des pulls régulièrement (toutes les dix minutes) afin de synchroniser les modifications externes (Tirer toutes les modifications).

    - Répliquer à la demande toutes les modifications apportées à la base de données hsqldb 2.5.1 à l'aide du contrôle de version du système (Pousser toutes les modifications).

- Ecriture d'une nouvelle interface [DataBase][24], responsable de tous les appels à la base de données.

- Mise en place d'un cache sur les identifiants, voir la méthode: [getIdentifier()][25], autorisant l'accès à un Contenu (fichier ou dossier) sans accès à la base de données pour les appels ultérieurs.

- Gestion des doublons des noms des fichiers / dossiers par [Vues SQL][26]: Child, Twin, Uri, et Title générant des noms uniques s'il existe des doublons.  
Bien que cette fonctionnalité ne soit nécessaire que pour gDriveOOo, elle est implémentée globalement...

- Beaucoup d'autres correctifs...

### Ce qui a été fait pour la version 0.0.6:

- Utilisation du nouveau schéma: **vnd-microsoft://** comme revendiqué par [draft-king-vnd-urlscheme-03.txt][27]

- Aboutissement de la gestion des doublons des noms de fichiers / dossiers par des vues SQL dans HsqlDB:
  - Une vue [**Twin**][28] regroupant tous les doublons par dossier parent et les ordonnant par date de création, date de modification.
  - Une vue [**Uri**][29] générant des indexes uniques pour chaque doublon.
  - Une vue [**Title**][30] générant des nom uniques pour chaque doublon.
  - Une vue récursive [**Path**][31] pour générer un chemin unique pour chaque fichier/dossier.

- Création d'un [ParameterizedContentProvider][32] capable de répondre aux deux types d'Urls supportées (nommées et anonymes).  
  Des expressions régulières (regex), déclarées dans le [fichier de configuration de l'UCB][33], sont maintenant utilisées par OpenOffice/LibreOffice pour envoyer les Urls au ContentProvider approprié.

- Utilisation de la nouvelle struct UNO [DateTimeWithTimezone][34] fournie par l'extension [jdbcDriverOOo][35] depuis sa version 0.0.4.  
  Bien que cette struct existe déjà dans LibreOffice, sa création était nécessaire afin de rester compatible avec OpenOffice (voir [Demande d'amélioration 128560][36]).

- Modification de l'interface [Replicator][23], afin de permettre:
  - De choisir l'ordre de synchronisation des données (locales d'abord puis distantes ensuite ou inversement).
  - La synchronisation des modifications locales par des opérations atomiques effectuées dans l'ordre chronologique pour supporter pleinement le travail hors ligne.  
  Pour ce faire, trois procédures SQL [GetPushItems][37], [GetPushProperties][38] et [UpdatePushItems][39] sont utilisées pour chaque utilisateur ayant accédé à ses fichiers / dossiers.

- Réécriture de la [fenêtre des options][40] accessible par : **Outils -> Options -> Internet -> oneDriveOOo** afin de permettre :
  - L'accès aux deux fichiers journaux concernant les activités de l'UCP et du réplicateur de données.
  - Le choix de l'ordre de synchronisation.
  - La modification de l'intervalle entre deux synchronisations.
  - L'accès à la base de données HsqlDB 2.7.1 sous-jacente gérant vos métadonnées Microsoft oneDrive.

- La présence ou l'absence d'une barre oblique finale dans l'Url est maintenant prise en charge.

- Beaucoup d'autres correctifs...

### Que reste-t-il à faire pour la version 0.0.6:

- Ajouter de nouvelles langue pour l'internationalisation...

- Tout ce qui est bienvenu...

[1]: <img/oneDriveOOo.png>
[2]: <https://prrvchr.github.io/oneDriveOOo>
[3]: <https://prrvchr.github.io/oneDriveOOo/source/oneDriveOOo/registration/TermsOfUse_fr>
[4]: <https://prrvchr.github.io/oneDriveOOo/source/oneDriveOOo/registration/PrivacyPolicy_fr>
[5]: <https://prrvchr.github.io/oneDriveOOo/README_fr#historique>
[6]: <https://prrvchr.github.io/README_fr>
[7]: <https://fr.libreoffice.org/download/telecharger-libreoffice/>
[8]: <https://www.openoffice.org/fr/Telecharger/>
[9]: <https://github.com/prrvchr/oneDriveOOo>
[10]: <https://github.com/prrvchr/oneDriveOOo/issues/new>
[11]: <http://hsqldb.org/>
[12]: <https://wiki.documentfoundation.org/Documentation/HowTo/Install_the_correct_JRE_-_LibreOffice_on_Windows_10/fr>
[13]: <https://adoptium.net/releases.html?variant=openjdk11>
[14]: <https://bugs.documentfoundation.org/show_bug.cgi?id=139538>
[15]: <https://prrvchr.github.io/HsqlDBembeddedOOo/README_fr>
[16]: <https://prrvchr.github.io/OAuth2OOo/img/OAuth2OOo.png>
[17]: <https://github.com/prrvchr/OAuth2OOo/raw/master/OAuth2OOo.oxt>
[18]: <https://prrvchr.github.io/jdbcDriverOOo/img/jdbcDriverOOo.png>
[19]: <https://github.com/prrvchr/jdbcDriverOOo/raw/master/source/jdbcDriverOOo/dist/jdbcDriverOOo.oxt>
[20]: <https://github.com/prrvchr/oneDriveOOo/raw/master/source/oneDriveOOo/dist/oneDriveOOo.oxt>
[21]: <https://prrvchr.github.io/oneDriveOOo/README_fr#configuration>
[22]: <https://prrvchr.github.io/OAuth2OOo/README_fr>
[23]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/replicator.py>
[24]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/database.py>
[25]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/datasource.py>
[26]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py>
[27]: <https://datatracker.ietf.org/doc/html/draft-king-vnd-urlscheme-00>
[28]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L165>
[29]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L175>
[30]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L195>
[31]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L215>
[32]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/ucp/parameterizedprovider.py>
[33]: <https://github.com/prrvchr/oneDriveOOo/blob/master/source/oneDriveOOo/oneDriveOOo.xcu#L19>
[34]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/rdb/idl/io/github/prrvchr/css/util/DateTimeWithTimezone.idl>
[35]: <https://prrvchr.github.io/jdbcDriverOOo/README_fr>
[36]: <https://bz.apache.org/ooo/show_bug.cgi?id=128560>
[37]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L481>
[38]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L524>
[39]: <https://github.com/prrvchr/oneDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L463>
[40]: <https://github.com/prrvchr/oneDriveOOo/tree/master/uno/lib/uno/options/ucb>
