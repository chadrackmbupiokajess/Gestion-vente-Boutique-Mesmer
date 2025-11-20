import sqlite3

def initialiser_db():
    """
    Initialise la base de données et crée les tables si elles n'existent pas.
    """
    conn = sqlite3.connect('gestion_ventes.db')
    cursor = conn.cursor()

    # Table Produits
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Produits (
        id TEXT PRIMARY KEY,
        nom TEXT NOT NULL UNIQUE,
        description TEXT,
        prix_vente REAL NOT NULL,
        quantite_stock INTEGER NOT NULL
    );
    """)

    # Table Clients
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        contact TEXT
    );
    """)

    # Table Ventes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total REAL NOT NULL,
        client_id INTEGER,
        FOREIGN KEY (client_id) REFERENCES Clients(id)
    );
    """)

    # Table Details_Vente
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
    conn = sqlite3.connect('gestion_ventes.db')
    conn.row_factory = sqlite3.Row
    return conn

def ajouter_client(nom, contact):
    """Ajoute un nouveau client et retourne son ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        nom_formate = nom.title()
        cursor.execute("INSERT INTO Clients (nom, contact) VALUES (?, ?)", (nom_formate, contact))
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

if __name__ == '__main__':
    initialiser_db()
