🇫🇷 Version française | [🇬🇧 English version](SECURITY.md)

---

# Politique de sécurité

## Versions supportées

Ce projet suit une seule branche `main` continue. Il n'y a pas de branches de release maintenues ; seul le dernier commit sur `main` est supporté.

## Signaler une vulnérabilité

Merci de **ne pas** ouvrir d'issue GitHub publique pour une vulnérabilité de sécurité.

Utilisez plutôt le signalement privé de GitHub : allez dans l'onglet [Security](https://github.com/MarvinLeRouge/Stamped/security/advisories/new) de ce dépôt et cliquez sur "Report a vulnerability". Le signalement reste privé jusqu'à ce qu'un correctif soit disponible.

Ce projet est maintenu par un seul développeur, les délais de réponse sont donc du best-effort, sans garantie de SLA.

## Périmètre

Dans le périmètre : l'API backend (`backend/`), l'application frontend (`frontend/`), la CLI (`stamped start` / `stamped index` / `stamped status`), et la façon dont l'app lit les fichiers photo/GPX locaux et stocke les données dans `data/`.

Hors périmètre : les services tiers appelés à l'import (serveurs de tuiles OSM, OpenTopoData, Nominatim). Signalez les problèmes liés à ces services directement à leurs mainteneurs respectifs.

## Particularités d'une application local-first

Stamped n'a ni authentification, ni comptes, ni surface d'attaque réseau au-delà des trois appels sortants décrits dans la section [Confidentialité](README.fr.md#-confidentialité) du README (tuiles OSM, OpenTopoData, Nominatim), tous en lecture seule, mis en cache localement, et qui ne transportent jamais le contenu des photos. Le serveur FastAPI n'écoute que sur `localhost` et est conçu pour tourner sur une seule machine de confiance, pas pour être exposé sur un réseau.
