# Aldais Portal Prélèvement à venir

Affiche dans le portail client (page **Mon compte**) les prélèvements SEPA à venir, afin que le client B2B puisse anticiper les débits sur son compte bancaire.

## Fonctionnement

Le bloc apparaît dans la colonne latérale de la page **Mon compte**, sous le lien vers les informations du compte. Il est masqué s'il n'y a aucun prélèvement à venir.

Chaque ligne affiche la date d'échéance et le montant total prélevé pour ce client à cette date, trié par ordre chronologique :

```
Prélèvement(s) à venir
31/05/2026          1 722,60 €
15/06/2026            850,00 €
```

## Critères de sélection des prélèvements

Un prélèvement est affiché si les conditions suivantes sont toutes remplies :

- Le batch de paiement est de type **SEPA Prélèvement** (code méthode `sdd`)
- La date d'échéance du batch est **aujourd'hui ou dans le futur**
- L'état du batch est **Nouveau** (`draft`) ou **Envoyé** (`sent`) — une fois réconcilié, le prélèvement a déjà eu lieu
- Le paiement concerne le client connecté ou l'un des contacts rattachés à sa société (`commercial_partner_id`)

Si un même batch contient plusieurs paiements pour le même client, les montants sont additionnés sur une seule ligne.

## Dépendances

- `portal`
- `account_batch_payment`

## Version

`17.0.1.0.0` — compatible Odoo 17
