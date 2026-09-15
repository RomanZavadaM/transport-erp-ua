# TransportERP-UA — Français

Statut de la traduction : `current`  
Source canonique : [`README.md`](../../../README.md)

**La langue canonique du projet est l’ukrainien.** En cas de divergence entre cette traduction et la version ukrainienne, le texte ukrainien prévaut.

TransportERP-UA est un système web destiné à une entreprise de transport ukrainienne. Il couvre la gestion des autobus et des conducteurs, les itinéraires et horaires, la planification des trajets, les services opérationnels, l’autorisation de mise en ligne, les contrôles préalables, les feuilles de route, le mouvement réel, le kilométrage, le carburant, la maintenance et les réparations, les documents, les rapports, les rôles et l’audit.

## Référence d’architecture

Version actuelle : **v1.3**.

Décisions principales :

- monolithe modulaire pour les premières versions de production ;
- PostgreSQL comme source transactionnelle de vérité ;
- `Trip` et `Duty` sont des concepts de domaine distincts ;
- un Duty peut contenir plusieurs Trips ;
- Release appartient à Duty ;
- Waybill est basé sur Duty et peut couvrir plusieurs Trips ;
- les données planifiées et réelles sont séparées ;
- l’historique clôturé et les versions de documents sont immuables ;
- les corrections créent de nouvelles versions au lieu de réécrire l’historique ;
- les changements critiques d’état utilisent des commandes métier explicites ;
- l’audit et les événements opérationnels sont append-only ;
- PostgreSQL protège l’affectation des ressources en situation de concurrence.

La documentation canonique complète est maintenue en ukrainien dans [`/docs`](../../).
