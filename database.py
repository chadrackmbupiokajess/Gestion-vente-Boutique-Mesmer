import sqlite3
import bcrypt

def initialiser_db():
    """
    Initialise la base de données et crée les tables si elles n'existent pas.
    Gère également les migrations de schéma (ajout de colonnes).
    """
    conn = sqlite3.connect('gestion_ventes.db')
    cursor = conn.cursor()

    # --- Migrations ---
    try:
        cursor.execute("ALTER TABLE Produits ADD COLUMN prix_achat REAL DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError: pass # Colonne déjà existante

    try:
        cursor.execute("ALTER TABLE Clients ADD COLUMN bonus_points INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError: pass # Colonne déjà existante

    # --- Création des tables ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Produits (
        id TEXT PRIMARY KEY, nom TEXT NOT NULL UNIQUE, description TEXT,
        prix_achat REAL DEFAULT 0, prix_vente REAL NOT NULL, quantite_stock INTEGER NOT NULL
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT NOT NULL, contact TEXT,
        bonus_points INTEGER DEFAULT 0
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total REAL NOT NULL, client_id INTEGER,
        FOREIGN KEY (client_id) REFERENCES Clients(id)
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Details_Vente (
        id INTEGER PRIMARY KEY AUTOINCREMENT, vente_id INTEGER NOT NULL, produit_id TEXT NOT NULL,
        quantite INTEGER NOT NULL, prix_unitaire REAL NOT NULL,
        FOREIGN KEY (vente_id) REFERENCES Ventes(id), FOREIGN KEY (produit_id) REFERENCES Produits(id)
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'vendeur'))
    );""")

    # --- Création de l'admin par défaut ---
    cursor.execute("SELECT * FROM Utilisateurs WHERE role = 'admin'")
    if not cursor.fetchone():
        hashed_password = bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO Utilisateurs (username, password, role) VALUES (?, ?, ?)",
                       ("admin", hashed_password, 'admin'))

    conn.commit()
    conn.close()

def get_db_connection():
    """Crée et retourne une connexion à la base de données."""
    conn = sqlite3.connect('gestion_ventes.db', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def verifier_utilisateur(username, password):
    """Vérifie les identifiants de l'utilisateur et retourne ses informations s'ils sont corrects."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM Utilisateurs WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return user
    return None

def lister_utilisateurs():
    """Retourne la liste de tous les utilisateurs."""
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role FROM Utilisateurs ORDER BY username").fetchall()
    conn.close()
    return users

def ajouter_utilisateur(username, password, role):
    """Ajoute un nouvel utilisateur avec un mot de passe haché."""
    conn = get_db_connection()
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn.execute("INSERT INTO Utilisateurs (username, password, role) VALUES (?, ?, ?)",
                     (username, hashed_password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError: # Nom d'utilisateur déjà pris
        return False
    finally:
        conn.close()

def find_or_create_client(nom, contact):
    """Cherche un client par nom et contact. S'il n'existe pas, le crée."""
    conn = get_db_connection()
    nom_formate = nom.title()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Clients WHERE nom = ? AND contact = ?", (nom_formate, contact))
    client = cursor.fetchone()
    if client:
        conn.close()
        return client['id']
    else:
        cursor.execute("INSERT INTO Clients (nom, contact, bonus_points) VALUES (?, ?, ?)", (nom_formate, contact, 0))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id

def modifier_client(client_id, nom, contact):
    """Modifie un client existant."""
    conn = get_db_connection()
    conn.execute("UPDATE Clients SET nom = ?, contact = ? WHERE id = ?", (nom.title(), contact, client_id))
    conn.commit()
    conn.close()

def supprimer_client(client_id):
    """Supprime un client."""
    conn = get_db_connection()
    conn.execute("DELETE FROM Clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()

def incrementer_points_bonus(client_id):
    """Incrémente les points de bonus d'un client."""
    conn = get_db_connection()
    conn.execute("UPDATE Clients SET bonus_points = bonus_points + 1 WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()

def get_client_contact(client_id):
    """Récupère le contact d'un client par son ID."""
    conn = get_db_connection()
    contact = conn.execute("SELECT contact FROM Clients WHERE id = ?", (client_id,)).fetchone()
    conn.close()
    return contact['contact'] if contact else None

if __name__ == '__main__':
    initialiser_db()
