# Cahier de Charges - Application de Gestion de Vente

Ce document détaille les fonctionnalités prévues pour l'application de gestion de vente développée en Python avec une base de données SQLite.

---

## Phase 1 : Fonctionnalités de Base (Le cœur du système)

### 1. Gestion des Produits
- **Ajouter** un nouveau produit (nom, description, prix de vente, quantité en stock).
- **Modifier** les informations d'un produit existant.
- **Supprimer** un produit.
- **Consulter** la liste de tous les produits et voir les détails d'un produit spécifique.

### 2. Gestion des Ventes
- Enregistrer une nouvelle vente :
    - Sélectionner un ou plusieurs produits.
    - Spécifier la quantité pour chaque produit.
    - Calculer automatiquement le montant total.
    - Valider la vente.
- **Consulter** l'historique des ventes.

### 3. Gestion de l'Inventaire (Stock)
- Mise à jour **automatique** du stock après chaque vente.
- Possibilité de mettre à jour **manuellement** le stock.
- Alertes ou indicateurs visuels pour les produits avec un stock faible.

---

## Phase 2 : Fonctionnalités Intermédiaires (Pour une meilleure gestion)

### 4. Gestion des Clients
- Ajouter/Modifier/Supprimer des clients (nom, prénom, contact).
- Associer une vente à un client pour suivre son historique d'achats.

### 5. Rapports et Statistiques
- Générer des rapports de ventes sur une période donnée (jour, semaine, mois).
- Afficher les produits les plus vendus.
- Calculer le chiffre d'affaires et les bénéfices sur une période.
- Rapport sur l'état actuel de l'inventaire.

---

## Phase 3 : Fonctionnalités Avancées (Pour une application complète)

### 6. Interface Utilisateur
- **Option A (Simple) :** Une interface en ligne de commande (CLI).
- **Option B (Graphique) :** Une interface graphique (GUI) avec une bibliothèque comme **Tkinter**, **PyQt** ou **CustomTkinter**.

### 7. Gestion des Utilisateurs
- Créer différents types de comptes (ex: Vendeur, Administrateur).
- Gérer les permissions (ex: un vendeur peut faire des ventes mais ne peut pas modifier les produits).

---

## Structure de la Base de Données SQLite

Pour supporter ces fonctionnalités, voici les tables proposées :

### Table `Produits`
```sql
CREATE TABLE Produits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    description TEXT,
    prix_vente REAL NOT NULL,
    quantite_stock INTEGER NOT NULL
);
```

### Table `Ventes`
```sql
CREATE TABLE Ventes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total REAL NOT NULL,
    client_id INTEGER,
    FOREIGN KEY (client_id) REFERENCES Clients(id)
);
```

### Table `Details_Vente` (Table de liaison)
```sql
CREATE TABLE Details_Vente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vente_id INTEGER NOT NULL,
    produit_id INTEGER NOT NULL,
    quantite INTEGER NOT NULL,
    prix_unitaire REAL NOT NULL,
    FOREIGN KEY (vente_id) REFERENCES Ventes(id),
    FOREIGN KEY (produit_id) REFERENCES Produits(id)
);
```

### Table `Clients`
```sql
CREATE TABLE Clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    contact TEXT
);
```
