🇫🇷 Version française | [🇬🇧 English version](user_guide.md)

---

# Guide utilisateur - Stamped

## Vue d'ensemble

Stamped transforme un dossier de photos et de traces GPX en une carte personnelle de tous les endroits visités. On lui pointe un dossier ; elle lit les données EXIF et GPX, regroupe les photos en sorties ("quests"), et affiche le tout sur une carte basée sur OpenStreetMap. Voir [docs/product-context.md](../product-context.fr.md) pour le concept sous-jacent.

## Démarrer l'app

```bash
stamped start
```

Ouvre l'app dans le navigateur à `http://localhost:8421`. Voir [docs/operations.md](../operations.fr.md) pour l'installation et la configuration.

## Importer des photos

> Le déclenchement d'import depuis l'interface décrit dans des versions antérieures du projet n'est pas encore disponible - démarrer un import nécessite actuellement une requête HTTP manuelle. Voir [docs/operations.md](../operations.fr.md) pour la commande exacte, et la [roadmap](../roadmap.fr.md) pour le câblage CLI/UI prévu.

Une fois l'import démarré, la carte se remplit progressivement : les positions des photos apparaissent d'abord (GPS EXIF ou interpolation GPX), les thumbnails suivent peu après.

## La carte

- Les photos géolocalisées apparaissent sous forme de marqueurs, regroupés en clusters au dézoom.
- Cliquer sur un cluster zoome et le déplie ; cliquer sur un marqueur seul ouvre la photo.
- Changer de couche de carte (OpenStreetMap, topographique, satellite) via le sélecteur de couche.
- Les traces GPX des quests visibles sont dessinées sous forme de polylines.

## Les quests

Une quest est une sortie : un ensemble de photos et de traces GPX prises à proximité temporelle les unes des autres (par défaut, moins de 6 heures d'écart - configurable, voir [docs/operations.md](../operations.fr.md)). La sidebar liste toutes les quests ; en sélectionner une ouvre sa **storyline**, une liste chronologique déroulante de ses photos.

- **Renommer une quest** depuis le panneau storyline ; laisser le nom vide pour revenir au nom automatique basé sur la date.
- **Exporter la trace GPX d'une quest** depuis le panneau storyline.
- **Profil d'élévation** - un panneau escamotable sous la carte montre l'altitude le long de la trace GPX de la quest ; survoler la storyline ou le curseur du graphique met en évidence le point correspondant dans les deux.

## Photos orphelines

Une photo sans position GPS utilisable (pas de GPS EXIF, non couverte par l'interpolation GPX) est une "orpheline". Les orphelines sont listées séparément et peuvent être placées sur la carte :

- **Individuellement** - clic pour placer une photo orpheline seule à un point choisi sur la carte.
- **En masse** - placer toutes les orphelines d'une quest d'un coup, à la position médiane chronologique des points GPS connus de cette quest.

Les photos sans aucune quest (`quest_id` non défini) apparaissent dans une vue dédiée "photos sans quest".

## Supprimer une photo

Supprimer une photo la retire de l'app (enregistrement en base et thumbnail) mais ne touche jamais au fichier original sur le disque. Les photos supprimées sont mémorisées pour ne pas être réimportées si l'import est relancé sur le même dossier.

## Parcourir toutes les photos

Un explorateur global liste toutes les photos importées, indépendamment du regroupement par quest, avec un filtre sur le statut orphelin.

## Fonctionner hors-ligne

Après le premier import d'une zone géographique, Stamped fonctionne entièrement hors-ligne : les tuiles de carte et les données d'élévation sont mises en cache localement. Voir [docs/operations.md](../operations.fr.md#appels-réseau) pour le détail exact de ce qui est récupéré et quand.
