🇫🇷 Version française | [🇬🇧 English version](product-context.md)

---

# Contexte produit - Stamped

## Concept

Les applications photo classiques demandent de taguer, organiser et décrire. Stamped ne fait pas ça. On lui pointe un dossier, et elle lit les données EXIF et les traces GPX, détecte automatiquement les sorties, place chaque photo sur une carte, et montre d'un coup d'œil l'étendue du territoire documenté.

Chaque photo géolocalisée est une preuve de présence. Stamped traite la collection comme un relevé géographique, pas comme un album.

## Utilisateur cible

Un utilisateur unique gérant sa propre collection de photos personnelles sur sa propre machine. Pas de support multi-utilisateur, pas de comptes, pas de fonctions de partage. Voir [ADR 0001](adr/0001-local-first-no-cloud.md) pour la justification du local-first.

## Vocabulaire clé

| Terme | Signification |
|---|---|
| `quest` | Une sortie - un ensemble de photos et de traces GPX regroupées par proximité temporelle (voir [ADR 0005](adr/0005-quest-as-canonical-term.md), [ADR 0006](adr/0006-quest-detection-temporal-clustering.md)) |
| `orphan` | Une photo sans position géographique (pas de GPS EXIF, non couverte par l'interpolation GPX) |
| `thumb` | Une vignette générée, stockée sur le filesystem, jamais en base de données |

## Fonctionnalités

- **Carte de conquête** - toutes les photos géolocalisées sur une carte OSM, regroupées par niveau de zoom ; filtre par quest, plage de dates ou zone
- **Détection des quests** - sorties auto-détectées par clustering temporel (écart configurable) ; quests renommables
- **Storyline** - liste chronologique déroulante des photos par quest, avec horodatage, vignettes et actions inline
- **Support GPX** - import de traces, affichage des polylines par fichier, interpolation de position pour les photos sans GPS, export GPX par quest
- **Gestion des orphelines** - photos sans coordonnées placées individuellement sur la carte (clic pour placer) ou en masse via le point médian chronologique des positions GPS de la quest
- **Suppression de photo** - retire l'enregistrement DB et la vignette générée ; le fichier original n'est jamais touché ; les hash supprimés sont mis en liste noire pour éviter la réindexation
- **Offline-first** - tuiles OSM mises en cache localement après le premier affichage ; données d'élévation enrichies une seule fois à l'import ; fonctionnement entièrement hors-ligne après le premier passage
- **Privé par conception** - pas de compte, pas de synchronisation cloud, pas d'analytics

## Non-objectifs

- Comptes multi-utilisateurs ou partage
- Stockage ou synchronisation cloud
- Édition de photos
- Fonctions sociales (commentaires, likes, flux public)
