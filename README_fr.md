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
# Documentation

**This [document][3] in English.**

**L'utilisation de ce logiciel vous soumet à nos [Conditions d'utilisation][4] et à notre [Politique de protection des données][5].**

# version [1.0.5][6]

## Introduction:

**mDriveOOo** fait partie d'une [Suite][7] d'extensions [LibreOffice][8] ~~et/ou [OpenOffice][9]~~ permettant de vous offrir des services inovants dans ces suites bureautique.  
Cette extension vous permet de travailler dans LibreOffice sur vos fichiers Microsoft OneDrive, même hors ligne.

Etant un logiciel libre je vous encourage:
- A dupliquer son [code source][10].
- A apporter des modifications, des corrections, des ameliorations.
- D'ouvrir un [dysfonctionnement][11] si nécessaire.

Bref, à participer au developpement de cette extension.
Car c'est ensemble que nous pouvons rendre le Logiciel Libre plus intelligent.

___

## Prérequis:

Afin de profiter des dernières versions des bibliothèques Python utilisées dans OAuth2OOo, la version 2 de Python a été abandonnée au profit de **Python 3.8 minimum**.  
Cela signifie que **mDriveOOo ne supporte plus OpenOffice et LibreOffice 6.x sous Windows depuis sa version 1.0.0**.
Je ne peux que vous conseiller **de migrer vers LibreOffice 7.x**.

mDriveOOo utilise une base de données locale [HsqlDB][12] version 2.7.2.  
HsqlDB étant une base de données écrite en Java, son utilisation nécessite [l'installation et la configuration][13] dans LibreOffice / OpenOffice d'un **JRE version 11 ou ultérieure**.  
Je vous recommande [Adoptium][14] comme source d'installation de Java.

Si vous utilisez **LibreOffice sous Linux**, vous êtes sujet au [dysfonctionnement 139538][15]. Pour contourner le problème, veuillez **désinstaller les paquets** avec les commandes:
- `sudo apt remove libreoffice-sdbc-hsqldb` (pour désinstaller le paquet libreoffice-sdbc-hsqldb)
- `sudo apt remove libhsqldb1.8.0-java` (pour désinstaller le paquet libhsqldb1.8.0-java)

Si vous souhaitez quand même utiliser la fonctionnalité HsqlDB intégré fournie par LibreOffice, alors installez l'extension [HyperSQLOOo][16].  

___

## Installation:

Il semble important que le fichier n'ait pas été renommé lors de son téléchargement.  
Si nécessaire, renommez-le avant de l'installer.

- [![OAuth2OOo logo][17]][18] Installer l'extension **[OAuth2OOo.oxt][19]** [![Version][20]][19]

    Vous devez d'abord installer cette extension, si elle n'est pas déjà installée.

- [![jdbcDriverOOo logo][21]][22] Installer l'extension **[jdbcDriverOOo.oxt][23]** [![Version][24]][23]

    Vous devez installer cette extension, si elle n'est pas déjà installée.

- ![mDriveOOo logo][25] Installer l'extension **[mDriveOOo.oxt][26]** [![Version][27]][26]

Redémarrez LibreOffice / OpenOffice après l'installation.

___

## Utilisation:

**Ouvrir votre OneDrive Microsoft:**

Dans: **Fichier -> Ouvrir** saisir dans la première liste déroulante:

- Pour une Url nommée: **vnd-microsoft://votre_adresse@votre_fournisseur**  

ou

- Pour une url non nommée (anonyme): **vnd-microsoft:///**

Et validez non pas par le bouton **Ouvrir** mais par la touche **Entrée**.

Si vous ne donnez pas **votre_adresse@votre_fournisseur**, elle vous sera demandée...

Les Urls anonymes vous permettent de rester anonyme (votre compte n'apparaît pas dans l'Url) tandis que les Urls nommées vous permettent d'accéder à plusieurs comptes simultanément.

Après avoir autorisé l'application [OAuth2OOo][18] à accéder à vos fichiers de votre Microsoft OneDrive, vos fichiers OneDrive devraient apparaître!!! normalement  :wink:

___

## A été testé avec:

* LibreOffice 7.3.7.2 - Lubuntu 22.04 - Python version 3.10.12

* LibreOffice 7.5.4.2(x86) - Windows 10 - Python version 3.8.16 (sous Lubuntu 22.04 / VirtualBox 6.1.38)

* LibreOffice 7.4.3.2(x64) - Windows 10(x64) - Python version 3.8.15 (sous Lubuntu 22.04 / VirtualBox 6.1.38)

* **Ne fonctionne pas avec OpenOffice** voir [dysfonctionnement 128569][28]. N'ayant aucune solution, je vous encourrage d'installer **LibreOffice**.

Je vous encourage en cas de problème :confused:  
de créer un [dysfonctionnement][11]  
J'essaierai de le résoudre :smile:

___

## Historique:

### Ce qui a été fait pour la version 0.0.5:

- Intégration et utilisation de la nouvelle version de Hsqldb 2.5.1.

- Ecriture d'une nouvelle interface [Replicator][29], lancé en arrière-plan (python Thread) responsable de:

    - Effectuer les procédures nécessaires lors de la création d'un nouvel utilisateur (Pull initial).

    - Effectuer des pulls régulièrement (toutes les dix minutes) afin de synchroniser les modifications externes (Tirer toutes les modifications).

    - Répliquer à la demande toutes les modifications apportées à la base de données hsqldb 2.5.1 à l'aide du contrôle de version du système (Pousser toutes les modifications).

- Ecriture d'une nouvelle interface [DataBase][30], responsable de tous les appels à la base de données.

- Mise en place d'un cache sur les identifiants, voir la méthode: [_getUser()][31], autorisant l'accès à un Contenu (fichier ou dossier) sans accès à la base de données pour les appels ultérieurs.

- Gestion des doublons des noms des fichiers / dossiers par [Vues SQL][32]: Child, Twin, Uri, et Title générant des noms uniques s'il existe des doublons.  
Bien que cette fonctionnalité ne soit nécessaire que pour gDriveOOo, elle est implémentée globalement...

- Beaucoup d'autres correctifs...

### Ce qui a été fait pour la version 0.0.6:

- Utilisation du nouveau schéma: **vnd-microsoft://** comme revendiqué par [draft-king-vnd-urlscheme-03.txt][33]

- Aboutissement de la gestion des doublons des noms de fichiers / dossiers par des vues SQL dans HsqlDB:
  - Une vue [**Twin**][34] regroupant tous les doublons par dossier parent et les ordonnant par date de création, date de modification.
  - Une vue [**Uri**][35] générant des indexes uniques pour chaque doublon.
  - Une vue [**Title**][36] générant des nom uniques pour chaque doublon.
  - Une vue récursive [**Path**][37] pour générer un chemin unique pour chaque fichier/dossier.

- Création d'un [Provider][38] capable de répondre aux deux types d'Urls supportées (nommées et anonymes).  
  Des expressions régulières (regex), déclarées dans le [fichier de configuration de l'UCB][39], sont maintenant utilisées par OpenOffice/LibreOffice pour envoyer les Urls au ContentProvider approprié.

- Utilisation de la nouvelle struct UNO [DateTimeWithTimezone][40] fournie par l'extension [jdbcDriverOOo][22] depuis sa version 0.0.4.  
  Bien que cette struct existe déjà dans LibreOffice, sa création était nécessaire afin de rester compatible avec OpenOffice (voir [Demande d'amélioration 128560][41]).

- Modification de l'interface [Replicator][29], afin de permettre:
  - De choisir l'ordre de synchronisation des données (locales d'abord puis distantes ensuite ou inversement).
  - La synchronisation des modifications locales par des opérations atomiques effectuées dans l'ordre chronologique pour supporter pleinement le travail hors ligne.  
  Pour ce faire, trois procédures SQL [GetPushItems][42], [GetPushProperties][43] et [UpdatePushItems][44] sont utilisées pour chaque utilisateur ayant accédé à ses fichiers / dossiers.

- Réécriture de la [fenêtre des options][45] accessible par : **Outils -> Options -> Internet -> mDriveOOo** afin de permettre :
  - L'accès aux deux fichiers journaux concernant les activités de l'UCP et du réplicateur de données.
  - Le choix de l'ordre de synchronisation.
  - La modification de l'intervalle entre deux synchronisations.
  - L'accès à la base de données HsqlDB 2.7.2 sous-jacente gérant vos métadonnées Microsoft oneDrive.

- La présence ou l'absence d'une barre oblique finale dans l'Url est maintenant prise en charge.

- Beaucoup d'autres correctifs...

### Ce qui a été fait pour la version 1.0.0:

- Renommage de l'extension OneDriveOOo en mDriveOOo.

### Ce qui a été fait pour la version 1.0.1:

- Mise en place de la gestion des fichiers partagés comme réclamé dans la demande d'amélioration, voir [dysfonctionnement 9][46].

- Le nom du dossier partagé peut être défini avant toute connexion dans: **Outils -> Options -> Internet -> mDriveOOo -> Gérer les documents partagés dans le dossier:**

- Beaucoup d'autres correctifs...

### Ce qui a été fait pour la version 1.0.2:

- L'absence ou l'obsolescence des extensions **OAuth2OOo** et/ou **jdbcDriverOOo** nécessaires au bon fonctionnement de **mDriveOOo** affiche désormais un message d'erreur.

- Encore plein d'autres choses...

### Ce qui a été fait pour la version 1.0.3:

- Prise en charge de la version 1.2.0 de l'extension **OAuth2OOo**. Les versions précédentes ne fonctionneront pas avec l'extension **OAuth2OOo** 1.2.0 ou ultérieure.

### Ce qui a été fait pour la version 1.0.4:

- Prise en charge de la version 1.2.1 de l'extension **OAuth2OOo**. Les versions précédentes ne fonctionneront pas avec l'extension **OAuth2OOo** 1.2.1 ou ultérieure.

### Ce qui a été fait pour la version 1.0.5:

- Prise en charge de la version 1.2.3 de l'extension **OAuth2OOo**. Correction du [dysfonctionnement #12][47]

### Que reste-t-il à faire pour la version 1.0.5:

- Ajouter de nouvelles langue pour l'internationalisation...

- Tout ce qui est bienvenu...

[1]: </img/drive.svg#collapse>
[2]: <https://prrvchr.github.io/mDriveOOo/>
[3]: <https://prrvchr.github.io/mDriveOOo>
[4]: <https://prrvchr.github.io/mDriveOOo/source/mDriveOOo/registration/TermsOfUse_fr>
[5]: <https://prrvchr.github.io/mDriveOOo/source/mDriveOOo/registration/PrivacyPolicy_fr>
[6]: <https://prrvchr.github.io/mDriveOOo/README_fr#historique>
[7]: <https://prrvchr.github.io/README_fr>
[8]: <https://fr.libreoffice.org/download/telecharger-libreoffice/>
[9]: <https://www.openoffice.org/fr/Telecharger/>
[10]: <https://github.com/prrvchr/mDriveOOo>
[11]: <https://github.com/prrvchr/mDriveOOo/issues/new>
[12]: <http://hsqldb.org/>
[13]: <https://wiki.documentfoundation.org/Documentation/HowTo/Install_the_correct_JRE_-_LibreOffice_on_Windows_10/fr>
[14]: <https://adoptium.net/releases.html?variant=openjdk11>
[15]: <https://bugs.documentfoundation.org/show_bug.cgi?id=139538>
[16]: <https://prrvchr.github.io/HyperSQLOOo/README_fr>
[17]: <https://prrvchr.github.io/OAuth2OOo/img/OAuth2OOo.svg#middle>
[18]: <https://prrvchr.github.io/OAuth2OOo/README_fr>
[19]: <https://github.com/prrvchr/OAuth2OOo/releases/latest/download/OAuth2OOo.oxt>
[20]: <https://img.shields.io/github/v/tag/prrvchr/OAuth2OOo?label=latest#right>
[21]: <https://prrvchr.github.io/jdbcDriverOOo/img/jdbcDriverOOo.svg#middle>
[22]: <https://prrvchr.github.io/jdbcDriverOOo/README_fr>
[23]: <https://github.com/prrvchr/jdbcDriverOOo/releases/latest/download/jdbcDriverOOo.oxt>
[24]: <https://img.shields.io/github/v/tag/prrvchr/jdbcDriverOOo?label=latest#right>
[25]: <img/mDriveOOo.svg#middle>
[26]: <https://github.com/prrvchr/mDriveOOo/releases/latest/download/mDriveOOo.oxt>
[27]: <https://img.shields.io/github/downloads/prrvchr/mDriveOOo/latest/total?label=v1.0.4#right>
[28]: <https://bz.apache.org/ooo/show_bug.cgi?id=128569>
[29]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/replicator.py>
[30]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/database.py>
[31]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/datasource.py#L127>
[32]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L154>
[33]: <https://datatracker.ietf.org/doc/html/draft-king-vnd-urlscheme-03>
[34]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L163>
[35]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L173>
[36]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L193>
[37]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L213>
[38]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/ucp/provider.py>
[39]: <https://github.com/prrvchr/mDriveOOo/blob/master/source/mDriveOOo/mDriveOOo.xcu#L42>
[40]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/rdb/idl/io/github/prrvchr/css/util/DateTimeWithTimezone.idl>
[41]: <https://bz.apache.org/ooo/show_bug.cgi?id=128560>
[42]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L512>
[43]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L557>
[44]: <https://github.com/prrvchr/mDriveOOo/blob/master/uno/lib/uno/ucb/dbqueries.py#L494>
[45]: <https://github.com/prrvchr/mDriveOOo/tree/master/uno/lib/uno/options/ucb>
[46]: <https://github.com/prrvchr/mDriveOOo/issues/9>
[47]: <https://github.com/prrvchr/gDriveOOo/issues/12>
