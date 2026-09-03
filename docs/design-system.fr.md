🇫🇷 Version française | [🇬🇧 English version](design-system.md)

---

# Design System - Stamped

**Type :** Référence de design - conventions visuelles observées dans le code.
**Périmètre :** Frontend (Vue 3, CSS scoped simple par composant, aucun framework CSS, aucun design token).

> Contrairement à certains projets voisins, il n'y a pas d'audit de design formel derrière ce document ni de fichier de tokens centralisé (variables CSS `:root`, config Tailwind, etc.). Les couleurs et les espacements sont codés en dur par composant. Ce document consigne les conventions réellement suivies, comme base de cohérence pour les travaux futurs, pas comme un ensemble de règles imposées.

## Vue d'ensemble

Stamped est une SPA à thème sombre, centrée sur la carte. La carte est la surface principale ; les panneaux latéraux (liste des quests, storyline, tableau de bord de statut) sont secondaires et denses, privilégiant la densité d'information à la décoration.

## Couleurs

Il n'existe pas de palette partagée ni de variables CSS custom ; chaque composant déclare ses propres valeurs hexadécimales dans un bloc `<style scoped>`. Valeurs récurrentes entre composants :

| Valeur | Usage typique |
|---|---|
| `#1a1a2e`, `#1e1e38`, `#0e0e22` | Surfaces de fond sombres |
| `#2a2a4e`, `#3b3b6e` | Fonds de panneaux/cartes, bordures |
| `#e85d04` | Accent / état actif |
| `#c0392b`, `#f87171`, `#ff6b6b` | Danger / actions destructives (suppression) |
| `#888`, `#666`, `#999`, `#aaa` | Texte secondaire/atténué |
| `#ccc`, `#f0f0f0` | Texte clair sur fond sombre |

Les nouveaux composants devraient réutiliser ces valeurs plutôt que d'en introduire de nouvelles pour le même rôle (fond, accent, danger, texte atténué).

## Typographie

La police du corps est définie une seule fois dans `frontend/src/assets/base.css` : `Inter` avec une pile de polices système en secours, `font-size: 15px`, `line-height: 1.6`. Le monospace (`font-family: monospace`) apparaît localement pour un petit nombre de valeurs techniques (hash, coordonnées).

## Layout

`App.vue` utilise une grille CSS racine : `grid-template-columns: minmax(180px, max-content) 1fr` (deux colonnes - sidebar et contenu), étendue à trois colonnes (`minmax(180px, max-content) minmax(180px, max-content) 1fr`) quand un second panneau latéral est ouvert. La carte occupe l'espace restant.

## Espacement

Aucune échelle d'espacement n'est définie ; les valeurs `gap` et `padding` sont choisies au cas par cas par composant, typiquement entre `0.2rem` et `1.5rem`. Le `border-radius` est petit et cohérent : `2px`-`4px` sur les boutons, tuiles et panneaux - aucun élément totalement arrondi (`border-radius: 50%`) ou anguleux (`0`) observé en dehors des contrôles de formulaire standards.

## Convention de nommage

Les noms de classes des composants suivent globalement BEM (`block__element--modifier`), ex. `.storyline__action-btn--pin`, `.unquested__action-btn--danger`. Ce n'est imposé par aucune règle de lint ; c'est une convention à suivre pour les nouveaux styles de composant.

## À faire / à éviter

### À faire
- Réutiliser une valeur hexadécimale existante pour le même rôle (fond, accent, danger, texte atténué) plutôt que d'en choisir une nouvelle.
- Suivre le motif `block__element--modifier` pour les nouvelles classes de composant.
- Garder le `border-radius` dans la plage `2px`-`4px` pour rester cohérent avec les composants existants.

### À éviter
- Introduire un framework CSS ou une nouvelle approche de style sans accord préalable - le projet n'en a volontairement aucun aujourd'hui.
- Ajouter des variables CSS globales sans migrer aussi les valeurs codées en dur existantes, ce qui laisserait deux systèmes concurrents en place.
