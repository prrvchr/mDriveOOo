**This [document](https://prrvchr.github.io/oneDriveOOo) in English.**

**L'utilisation de ce logiciel vous soumet à nos [Conditions d'utilisation](https://prrvchr.github.io/oneDriveOOo/oneDriveOOo/registration/TermsOfUse_fr) et à notre [Politique de protection des données](https://prrvchr.github.io/oneDriveOOo/oneDriveOOo/registration/PrivacyPolicy_fr).**

# version [0.0.5](https://prrvchr.github.io/oneDriveOOo/README_fr#historique)

## Introduction:

**oneDriveOOo** est une extension [LibreOffice](https://fr.libreoffice.org/download/telecharger-libreoffice/) et/ou [OpenOffice](https://www.openoffice.org/fr/Telecharger/) permettant de vous offrir des services inovants dans ces suites bureautique.  
Cette extension vous permet de travailler dans LibreOffice / OpenOffice sur vos fichiers Microsoft OneDrive, même hors ligne.

Etant un logiciel libre je vous encourage:
- A dupliquer son [code source](https://github.com/prrvchr/oneDriveOOo).
- A apporter des modifications, des corrections, des ameliorations.

Bref, à participer au developpement de cette extension.
Car c'est ensemble que nous pouvons rendre le Logiciel Libre plus intelligent.

## Prérequis:

oneDriveOOo utilise une base de données locale Hsqldb version 2.5.1.  
L'utilisation de Hsqldb nécessite l'installation et la configuration dans
LibreOffice / OpenOffice d'un **JRE version 1.8 minimum** (c'est-à-dire: Java version 8)

Parfois, il peut être nécessaire pour les utilisateurs de LibreOffice de ne pas avoir de pilote Hsqldb installé avec LibreOffice  
(vérifiez vos applications installées sous Windows ou votre gestionnaire de paquets sous Linux)  
Il semble que les versions 6.4.x et 7.x de LibreOffice aient résolu ce problème et sont capables de fonctionner simultanément avec différentes versions de pilote de Hsqldb.  
OpenOffice ne semble pas avoir besoin de cette solution de contournement.

## Installation:

Il semble important que le fichier n'ait pas été renommé lors de son téléchargement.  
Si nécessaire, renommez-le avant de l'installer.

- Installer l'extension [OAuth2OOo.oxt](https://github.com/prrvchr/OAuth2OOo/raw/master/OAuth2OOo.oxt) version 0.0.5.

Vous devez d'abord installer cette extension, si elle n'est pas déjà installée.

- Installer l'extension [oneDriveOOo.oxt](https://github.com/prrvchr/oneDriveOOo/raw/master/oneDriveOOo.oxt) version 0.0.5.

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

**Ouvrir votre OneDrive Microsoft:**

Dans: Fichier - Ouvrir - Nom de fichier saisir:

- **vnd.microsoft-apps://votre_compte/** 

ou

- **vnd.microsoft-apps:///**

Si vous ne donnez pas votre_compte, il vous sera demandé...

Après avoir autorisé l'application OAuthOOo à accéder à vos fichiers de votre Microsoft OneDrive, vos fichiers OneDrive devraient apparaître!!! normalement  ;-)

## A été testé avec:

* LibreOffice 6.4.4.2 - Ubuntu 20.04 -  LxQt 0.14.1

* LibreOffice 7.0.0.0.alpha1 - Ubuntu 20.04 -  LxQt 0.14.1

* OpenOffice 4.1.5 x86_64 - Ubuntu 20.04 - LxQt 0.14.1

* OpenOffice 4.2.0.Build:9820 x86_64 - Ubuntu 20.04 - LxQt 0.14.1

* LibreOffice 6.1.5.2 - Raspbian 10 buster - Raspberry Pi 4 Model B

* LibreOffice 6.4.4.2 (x64) - Windows 7 SP1

Je vous encourage en cas de problème :-(  
de créer une [issue](https://github.com/prrvchr/oneDriveOOo/issues/new)  
J'essaierai de la résoudre ;-)

## Historique:

### Ce qui a été fait pour la version 0.0.5:

- Intégration et utilisation de la nouvelle version de Hsqldb 2.5.1.

- Ecriture d'une nouvelle interface [Replicator](https://github.com/prrvchr/oneDriveOOo/blob/master/CloudUcpOOo/python/clouducp/replicator.py), lancé en arrière-plan (python Thread) responsable de:

    - Effectuer les procédures nécessaires lors de la création d'un nouvel utilisateur (Pull initial).

    - Effectuer des pulls régulièrement (toutes les dix minutes) afin de synchroniser les modifications externes (Tirer toutes les modifications).

    - Répliquer à la demande toutes les modifications apportées à la base de données hsqldb 2.5.1 à l'aide du contrôle de version du système (Pousser toutes les modifications).

- Ecriture d'une nouvelle interface [DataBase](https://github.com/prrvchr/oneDriveOOo/blob/master/CloudUcpOOo/python/clouducp/database.py), responsable de tous les appels à la base de données.

- Mise en place d'un cache sur les identifiants, voir la méthode: [getIdentifier()](https://github.com/prrvchr/oneDriveOOo/blob/master/CloudUcpOOo/python/clouducp/datasource.py), autorisant l'accès à un Contenu (fichier ou dossier) sans accès à la base de données pour les appels ultérieurs.

- Gestion des doublons des noms des fichiers / dossiers par [Vues SQL](https://github.com/prrvchr/oneDriveOOo/blob/master/CloudUcpOOo/python/clouducp/dbqueries.py): Child, Twin, Uri, et Title générant des noms uniques s'il existe des doublons.  
Bien que cette fonctionnalité ne soit nécessaire que pour gDriveOOo, elle est implémentée globalement...

- Beaucoup d'autres correctifs...

### Que reste-t-il à faire pour la version 0.0.5:

- Écrire l'implémentation Pull Change dans la nouvelle interface [Replicator](https://github.com/prrvchr/oneDriveOOo/blob/master/CloudUcpOOo/python/clouducp/replicator.py).

- Ajouter de nouvelles langue pour l'internationalisation...

- Tout ce qui est bienvenu...
