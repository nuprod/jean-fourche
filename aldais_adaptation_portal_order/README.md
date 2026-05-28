# Aldais Adaptation Portal Commande

## Description

Ce module personnalise l'affichage des commandes clients dans le portail Odoo pour Jean Fourche / Aldais.

## Fonctionnalités

### 1. Colonne "Date de livraison" dans la liste des commandes

Dans **Portal → Commandes**, une colonne **Date de livraison** est ajoutée à gauche de la colonne "Date de la commande".

- Affiche le champ `commitment_date` du bon de commande (`sale.order`)
- Affiche **"en cours de planification"** si le champ est vide

### 2. Remplacement de la date dans la vue détail commande

Dans la fiche détail d'une commande, la section **"Date de livraison estimée"** affichait la date issue du bon de livraison (`picking.scheduled_date`).

Ce module la remplace par le champ `commitment_date` du bon de commande :

- Affiche la date d'engagement saisie sur la commande
- Affiche **"en cours de planification"** si le champ est vide

## Technique

| Élément | Valeur |
|---|---|
| Version Odoo | 17.0 |
| Dépendances | `sale`, `sale_stock` |
| Templates hérités | `sale.portal_my_orders`, `sale_stock.sale_order_portal_content_inherit_sale_stock` |
| Champ source | `sale.order.commitment_date` |

## Auteur

Aldais / NUprod — [www.nuprod.fr](http://www.nuprod.fr)
