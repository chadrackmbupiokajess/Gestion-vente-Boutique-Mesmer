import sqlite3

def initialiser_db():
    """
    Initialise la base de données et crée les tables si elles n'existent pas.
    Gère également les migrations de schéma (ajout de colonnes).
    """
    conn = sqlite3.connect('gestion_ventes.db')
    cursor = conn.cursor()

    # --- Migration: Ajouter la colonne prix_achat à Produits ---
    try:
        cursor.execute("ALTER TABLE Produits ADD COLUMN prix_achat REAL DEFAULT 0")
        conn.commit()
        print("Colonne 'prix_achat' ajoutée à la table Produits.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass  # La colonne existe déjà, c'est normal
        else:
            raise e

    # --- Migration: Ajouter la colonne bonus_points à Clients ---
    try:
        cursor.execute("ALTER TABLE Clients ADD COLUMN bonus_points INTEGER DEFAULT 0")
        conn.commit()
        print("Colonne 'bonus_points' ajoutée à la table Clients.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            pass  # La colonne existe déjà, c'est normal
        else:
            raise e

    # Création de la table Produits
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Produits (
        id TEXT PRIMARY KEY,
        nom TEXT NOT NULL UNIQUE,
        description TEXT,
        prix_achat REAL DEFAULT 0,
        prix_vente REAL NOT NULL,
        quantite_stock INTEGER NOT NULL
    );
    """)

    # Création de la table Clients
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        contact TEXT,
        bonus_points INTEGER DEFAULT 0
    );
    """)

    # Création de la table Ventes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total REAL NOT NULL,
        client_id INTEGER,
        FOREIGN KEY (client_id) REFERENCES Clients(id)
    );
    """)

    # Création de la table Details_Vente
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Details_Vente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vente_id INTEGER NOT NULL,
        produit_id TEXT NOT NULL,
        quantite INTEGER NOT NULL,
        prix_unitaire REAL NOT NULL,
        FOREIGN KEY (vente_id) REFERENCES Ventes(id),
        FOREIGN KEY (produit_id) REFERENCES Produits(id)
    );
    """)

    conn.commit()
    conn.close()

def get_db_connection():
    """Crée et retourne une connexion à la base de données."""
    conn = sqlite3.connect('gestion_ventes.db', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def find_or_create_client(nom, contact):
    """
    Cherche un client par nom et contact.
    S'il n'existe pas, le crée et retourne son ID.
    S'il existe, retourne son ID.
    """
    conn = get_db_connection()
    nom_formate = nom.title()
    
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Clients WHERE nom = ? AND contact = ?", (nom_formate, contact))
    existing_client = cursor.fetchone()
    
    if existing_client:
        conn.close()
        return existing_client['id']
    else:
        cursor.execute("INSERT INTO Clients (nom, contact, bonus_points) VALUES (?, ?, ?)", (nom_formate, contact, 0))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id

def ajouter_client(nom, contact):
    """Ajoute un nouveau client et retourne son ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        nom_formate = nom.title()
        cursor.execute("INSERT INTO Clients (nom, contact, bonus_points) VALUES (?, ?, ?)", (nom_formate, contact, 0))
        new_id = cursor.lastrowid
        conn.commit()
        return new_id
    finally:
        conn.close()

def modifier_client(client_id, nom, contact):
    """Modifie un client existant."""
    conn = get_db_connection()
    try:
        nom_formate = nom.title()
        conn.execute(
            "UPDATE Clients SET nom = ?, contact = ? WHERE id = ?",
            (nom_formate, contact, client_id)
        )
        conn.commit()
    finally:
        conn.close()

def supprimer_client(client_id):
    """Supprime un client."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM Clients WHERE id = ?", (client_id,))
        conn.commit()
    finally:
        conn.close()

def incrementer_points_bonus(client_id):
    """Incrémente les points de bonus d'un client."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Clients SET bonus_points = bonus_points + 1 WHERE id = ?", (client_id,))
        conn.commit()
    finally:
        conn.close()

def get_client_contact(client_id):
    """Récupère le contact d'un client par son ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT contact FROM Clients WHERE id = ?", (client_id,))
    contact = cursor.fetchone()
    conn.close()
    return contact['contact'] if contact else None

if __name__ == '__main__':
    initialiser_db()
