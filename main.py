import sqlite3
import random
import string
from functools import partial
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.list import TwoLineListItem, OneLineListItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.toast import toast

from database import initialiser_db, modifier_client, supprimer_client, ajouter_client as db_ajouter_client

# --- Fonctions DB (inchangées) ---
def get_db_connection():
    conn = sqlite3.connect('gestion_ventes.db')
    conn.row_factory = sqlite3.Row
    return conn

def lister_produits(search_term=""):
    conn = get_db_connection()
    query = "SELECT * FROM Produits WHERE nom LIKE ? ORDER BY nom"
    produits = conn.execute(query, ('%' + search_term + '%',)).fetchall()
    conn.close()
    return produits

def lister_produits_en_stock(search_term=""):
    conn = get_db_connection()
    query = "SELECT * FROM Produits WHERE quantite_stock > 0 AND nom LIKE ? ORDER BY nom"
    produits = conn.execute(query, ('%' + search_term + '%',)).fetchall()
    conn.close()
    return produits

def ajouter_produit(nom, desc, prix, stock):
    conn = get_db_connection()
    conn.execute("INSERT INTO Produits (id, nom, description, prix_vente, quantite_stock) VALUES (?, ?, ?, ?, ?)",
                 ('PROD-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)), nom.capitalize(), desc, prix, stock))
    conn.commit()
    conn.close()

def modifier_produit(produit_id, nom, desc, prix, stock):
    conn = get_db_connection()
    conn.execute("UPDATE Produits SET nom = ?, description = ?, prix_vente = ?, quantite_stock = ? WHERE id = ?",
                 (nom.capitalize(), desc, prix, stock, produit_id))
    conn.commit()
    conn.close()

def supprimer_produit(produit_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM Produits WHERE id = ?", (produit_id,))
    conn.commit()
    conn.close()

def lister_clients():
    conn = get_db_connection()
    clients = conn.execute("SELECT * FROM Clients ORDER BY nom").fetchall()
    conn.close()
    return clients

def lister_ventes():
    conn = get_db_connection()
    ventes = conn.execute("""
        SELECT V.id, V.date_vente, V.total, C.nom as client_nom
        FROM Ventes V
        LEFT JOIN Clients C ON V.client_id = C.id
        ORDER BY V.date_vente DESC
    """).fetchall()
    conn.close()
    return ventes

def enregistrer_vente(client_id, panier):
    conn = get_db_connection()
    try:
        total_vente = sum(item['produit']['prix_vente'] * item['quantite'] for item in panier)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Ventes (total, client_id) VALUES (?, ?)", (total_vente, client_id))
        vente_id = cursor.lastrowid
        for item in panier:
            produit = item['produit']
            quantite_vendue = item['quantite']
            cursor.execute("INSERT INTO Details_Vente (vente_id, produit_id, quantite, prix_unitaire) VALUES (?, ?, ?, ?)",
                           (vente_id, produit['id'], quantite_vendue, produit['prix_vente']))
            nouveau_stock = produit['quantite_stock'] - quantite_vendue
            cursor.execute("UPDATE Produits SET quantite_stock = ? WHERE id = ?", (nouveau_stock, produit['id']))
        conn.commit()
    finally:
        conn.close()

# --- Classes de dialogue améliorées pour la navigation au clavier ---
class BaseDialogContent(MDBoxLayout):
    def __init__(self, **kwargs):
        self.ok_action = kwargs.pop('ok_action', None)
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "12dp"
        self.size_hint_y = None
        self.fields = []

    def on_open(self):
        Window.bind(on_key_down=self._on_keyboard_down)
        if self.fields:
            self.fields[0].focus = True

    def on_dismiss(self):
        Window.unbind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, instance, keyboard, keycode, text, modifiers):
        if keycode in (13, 271):  # Enter or Numpad Enter
            # Si une action OK est définie, on l'exécute
            if self.ok_action:
                self.ok_action()
                return True
        if keycode == 43:  # Tab
            self.focus_next_field()
            return True

    def focus_next_field(self):
        try:
            current_focus = next(f for f in self.fields if f.focus)
            current_index = self.fields.index(current_focus)
            next_index = (current_index + 1) % len(self.fields)
            self.fields[next_index].focus = True
        except StopIteration:
            if self.fields:
                self.fields[0].focus = True

class ProductDialogContent(BaseDialogContent):
    def __init__(self, **kwargs):
        super().__init__(height="300dp", **kwargs)
        self.nom_field = MDTextField(hint_text="Nom du produit")
        self.desc_field = MDTextField(hint_text="Description")
        self.prix_field = MDTextField(hint_text="Prix de vente (Fc)", input_filter="float")
        self.stock_field = MDTextField(hint_text="Quantité en stock", input_filter="int")
        self.fields = [self.nom_field, self.desc_field, self.prix_field, self.stock_field]
        for field in self.fields:
            if self.ok_action:
                field.on_text_validate = self.ok_action
            self.add_widget(field)

class ClientDialogContent(BaseDialogContent):
    def __init__(self, **kwargs):
        super().__init__(height="180dp", **kwargs)
        self.nom_field = MDTextField(hint_text="Nom du client")
        self.contact_field = MDTextField(hint_text="Contact (tél, email, ...)")
        self.fields = [self.nom_field, self.contact_field]
        for field in self.fields:
            if self.ok_action:
                field.on_text_validate = self.ok_action
            self.add_widget(field)

class FinalizeSaleDialogContent(BaseDialogContent):
    def __init__(self, total, **kwargs):
        super().__init__(height="240dp", **kwargs)
        self.total_label = MDLabel(text=f"Total à payer : {total:,.2f} Fc", halign="center", font_style="H6")
        self.nom_field = MDTextField(hint_text="Nom du client (facultatif)")
        self.contact_field = MDTextField(hint_text="Contact (facultatif)")
        self.fields = [self.nom_field, self.contact_field]
        self.add_widget(self.total_label)
        for field in self.fields:
            if self.ok_action:
                field.on_text_validate = self.ok_action
            self.add_widget(field)

# --- Application Principale ---
class MainApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.taux_usd_vers_fc = 2800.0
        self.panier = []
        self.selected_item = None

    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.theme_style = "Light"
        initialiser_db()
        return Builder.load_file('main.kv')

    def on_start(self):
        self.update_all_lists()

    def update_all_lists(self):
        self.update_product_list()
        self.update_client_list()
        self.update_sales_list()

    def go_to_new_sale_screen(self):
        self.root.current = 'new_sale_screen'
        self.root.ids.search_results_list.clear_widgets()
        self.root.ids.sale_search_field.text = ""
        self.root.ids.sale_search_field.focus = True

    def go_to_main_screen(self):
        self.root.current = 'main_screen'
        self.update_all_lists()

    def search_products(self):
        self.update_product_list(self.root.ids.search_field.text)

    def search_products_for_sale(self):
        search_term = self.root.ids.sale_search_field.text
        results_list = self.root.ids.search_results_list
        results_list.clear_widgets()
        if search_term:
            for p in lister_produits_en_stock(search_term):
                item = TwoLineListItem(
                    text=f"{p['nom']}",
                    secondary_text=f"Stock: {p['quantite_stock']} | Prix: {p['prix_vente']:,.2f} Fc",
                    on_release=lambda x, produit=p: self.ask_quantity_for_product(produit)
                )
                item.product_data = p
                results_list.add_widget(item)

    def handle_sale_search_enter(self):
        search_field = self.root.ids.sale_search_field
        if not search_field.text and self.panier:
            self.validate_sale()
        else:
            self.select_first_product_from_search()

    def select_first_product_from_search(self):
        results_list = self.root.ids.search_results_list
        if not results_list.children:
            return
        first_item_widget = results_list.children[-1]
        product_data = first_item_widget.product_data
        self.ask_quantity_for_product(product_data)

    def ask_quantity_for_product(self, produit, *args):
        def add_action(quantity_field):
            self.add_to_cart(produit, quantity_field.text)

        quantity_field = MDTextField(hint_text="Quantité", input_filter="int")
        quantity_field.on_text_validate = lambda: add_action(quantity_field)

        self.dialog = MDDialog(
            title=f"Quantité pour {produit['nom']}",
            type="custom",
            content_cls=quantity_field,
            buttons=[
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="AJOUTER", on_release=lambda x: add_action(quantity_field)),
            ],
        )
        self.dialog.open()
        quantity_field.focus = True

    def add_to_cart(self, produit, quantity_text):
        self.dialog.dismiss()
        if not quantity_text: return
        try:
            quantity = int(quantity_text)
            if quantity <= 0 or quantity > produit['quantite_stock']: return
        except ValueError: return

        self.panier.append({'produit': produit, 'quantite': quantity})
        self.update_cart_list()
        self.root.ids.sale_search_field.text = ""
        self.root.ids.sale_search_field.focus = True
        self.search_products_for_sale()

    def update_cart_list(self):
        cart_list = self.root.ids.cart_list
        cart_list.clear_widgets()
        total = 0
        for item in self.panier:
            p, q = item['produit'], item['quantite']
            subtotal = p['prix_vente'] * q
            total += subtotal
            
            line_item = MDBoxLayout(adaptive_height=True, spacing="10dp")
            label = OneLineListItem(text=f"{q} x {p['nom']} - {subtotal:,.2f} Fc")
            delete_button = MDIconButton(icon="trash-can", on_release=partial(self.remove_from_cart, item))
            
            line_item.add_widget(label)
            line_item.add_widget(delete_button)
            cart_list.add_widget(line_item)
            
        self.root.ids.total_label.text = f"Total: {total:,.2f} Fc"

    def remove_from_cart(self, item, *args):
        self.panier.remove(item)
        self.update_cart_list()

    def validate_sale(self):
        if not self.panier: return
        total = sum(item['produit']['prix_vente'] * item['quantite'] for item in self.panier)
        
        def ok_action():
            self.finalize_and_save_sale(content_cls, print_ticket=False)
            
        content_cls = FinalizeSaleDialogContent(total=total, ok_action=ok_action)
        
        self.dialog = MDDialog(
            title="Finaliser la Vente",
            type="custom",
            content_cls=content_cls,
            buttons=[
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="OK", on_release=ok_action),
                MDIconButton(icon="printer", on_release=lambda x: self.finalize_and_save_sale(content_cls, print_ticket=True)),
            ],
        )
        content_cls.on_open()
        self.dialog.on_dismiss = content_cls.on_dismiss
        self.dialog.open()

    def finalize_and_save_sale(self, content, print_ticket):
        client_id = None
        nom_client = content.nom_field.text
        if nom_client:
            contact_client = content.contact_field.text
            client_id = db_ajouter_client(nom_client, contact_client)

        enregistrer_vente(client_id, self.panier)
        if print_ticket:
            toast("Impression du ticket...")

        self.dialog.dismiss()
        self.panier = []
        self.update_cart_list()
        self.go_to_main_screen()

    def update_product_list(self, search_term=""):
        product_list = self.root.ids.product_list
        product_list.clear_widgets()
        for p in lister_produits(search_term):
            prix_usd = p['prix_vente'] / self.taux_usd_vers_fc
            item = TwoLineListItem(
                text=f"{p['nom']}",
                secondary_text=f"Prix: {p['prix_vente']:,.2f} Fc (${prix_usd:,.2f}) | Stock: {p['quantite_stock']}",
                on_release=partial(self.show_product_choice_dialog, p)
            )
            product_list.add_widget(item)

    def update_client_list(self):
        client_list = self.root.ids.client_list
        client_list.clear_widgets()
        for c in lister_clients():
            item = TwoLineListItem(text=f"{c['nom']}", secondary_text=f"Contact: {c['contact']}",
                                 on_release=partial(self.show_client_choice_dialog, c))
            client_list.add_widget(item)

    def update_sales_list(self):
        sales_list = self.root.ids.sales_list
        sales_list.clear_widgets()
        for v in lister_ventes():
            client_name = v['client_nom'] if v['client_nom'] else "Client au comptant"
            item = TwoLineListItem(
                text=f"Vente #{v['id']} - {v['total']:,.2f} Fc",
                secondary_text=f"{v['date_vente']} - {client_name}"
            )
            sales_list.add_widget(item)
            
    def show_add_product_dialog(self):
        def ok_action():
            self.add_product_action(content_cls)
        content_cls = ProductDialogContent(ok_action=ok_action)
        self.dialog = MDDialog(
            title="Ajouter un Produit", type="custom", content_cls=content_cls,
            buttons=[
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="AJOUTER", on_release=ok_action),
            ],
        )
        content_cls.on_open()
        self.dialog.on_dismiss = content_cls.on_dismiss
        self.dialog.open()

    def add_product_action(self, content):
        ajouter_produit(content.nom_field.text, content.desc_field.text, float(content.prix_field.text), int(content.stock_field.text))
        self.update_product_list()
        self.dialog.dismiss()

    def show_product_choice_dialog(self, produit, *args):
        self.selected_item = produit
        self.dialog = MDDialog(
            title=f"Actions pour {produit['nom']}",
            buttons=[
                MDFlatButton(text="MODIFIER", on_release=self.show_edit_product_dialog),
                MDFlatButton(text="SUPPRIMER", on_release=self.show_delete_product_dialog),
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
            ],
        )
        self.dialog.open()

    def show_edit_product_dialog(self, *args):
        self.dialog.dismiss()
        def ok_action():
            self.edit_product_action(content_cls)
        content_cls = ProductDialogContent(ok_action=ok_action)
        content_cls.nom_field.text = self.selected_item['nom']
        content_cls.desc_field.text = self.selected_item['description']
        content_cls.prix_field.text = str(self.selected_item['prix_vente'])
        content_cls.stock_field.text = str(self.selected_item['quantite_stock'])
        
        self.dialog = MDDialog(
            title="Modifier un Produit", type="custom", content_cls=content_cls,
            buttons=[
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="SAUVEGARDER", on_release=ok_action),
            ],
        )
        content_cls.on_open()
        self.dialog.on_dismiss = content_cls.on_dismiss
        self.dialog.open()

    def edit_product_action(self, content):
        modifier_produit(
            self.selected_item['id'], content.nom_field.text, content.desc_field.text,
            float(content.prix_field.text), int(content.stock_field.text)
        )
        self.update_product_list()
        self.dialog.dismiss()

    def show_delete_product_dialog(self, *args):
        self.dialog.dismiss()
        self.dialog = MDDialog(
            title=f"Supprimer {self.selected_item['nom']}?", text="Cette action est irréversible.",
            buttons=[
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="SUPPRIMER", on_release=self.delete_product_action),
            ],
        )
        self.dialog.open()

    def delete_product_action(self, *args):
        supprimer_produit(self.selected_item['id'])
        self.update_product_list()
        self.dialog.dismiss()

    def show_add_client_dialog(self):
        def ok_action():
            self.add_client_action(content_cls)
        content_cls = ClientDialogContent(ok_action=ok_action)
        self.dialog = MDDialog(
            title="Ajouter un Client", type="custom", content_cls=content_cls,
            buttons=[
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="AJOUTER", on_release=ok_action),
            ],
        )
        content_cls.on_open()
        self.dialog.on_dismiss = content_cls.on_dismiss
        self.dialog.open()

    def add_client_action(self, content):
        db_ajouter_client(content.nom_field.text, content.contact_field.text)
        self.update_client_list()
        self.dialog.dismiss()

    def show_client_choice_dialog(self, client, *args):
        self.selected_item = client
        self.dialog = MDDialog(
            title=f"Actions pour {client['nom']}",
            buttons=[
                MDFlatButton(text="MODIFIER", on_release=self.show_edit_client_dialog),
                MDFlatButton(text="SUPPRIMER", on_release=self.show_delete_client_dialog),
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
            ],
        )
        self.dialog.open()

    def show_edit_client_dialog(self, *args):
        self.dialog.dismiss()
        def ok_action():
            self.edit_client_action(content_cls)
        content_cls = ClientDialogContent(ok_action=ok_action)
        content_cls.nom_field.text = self.selected_item['nom']
        content_cls.contact_field.text = self.selected_item['contact']
        
        self.dialog = MDDialog(
            title="Modifier un Client", type="custom", content_cls=content_cls,
            buttons=[
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="SAUVEGARDER", on_release=ok_action),
            ],
        )
        content_cls.on_open()
        self.dialog.on_dismiss = content_cls.on_dismiss
        self.dialog.open()

    def edit_client_action(self, content):
        modifier_client(self.selected_item['id'], content.nom_field.text, content.contact_field.text)
        self.update_client_list()
        self.dialog.dismiss()

    def show_delete_client_dialog(self, *args):
        self.dialog.dismiss()
        self.dialog = MDDialog(
            title=f"Supprimer {self.selected_item['nom']}?", text="Cette action est irréversible.",
            buttons=[
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="SUPPRIMER", on_release=self.delete_client_action),
            ],
        )
        self.dialog.open()

    def delete_product_action(self, *args):
        supprimer_produit(self.selected_item['id'])
        self.update_product_list()
        self.dialog.dismiss()

    def show_rate_dialog(self):
        rate_field = MDTextField(text=str(self.taux_usd_vers_fc), hint_text="Taux de change (1 USD pour X Fc)", input_filter="float")
        self.dialog = MDDialog(
            title="Taux de Change", type="custom", content_cls=rate_field,
            buttons=[
                MDFlatButton(text="ANNULER", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="OK", on_release=lambda x: self.update_rate_action(rate_field.text)),
            ],
        )
        self.dialog.open()

    def update_rate_action(self, new_rate_text):
        try:
            self.taux_usd_vers_fc = float(new_rate_text)
            self.update_product_list()
            self.dialog.dismiss()
        except ValueError:
            print("Erreur: Le taux doit être un nombre.")

if __name__ == '__main__':
    MainApp().run()
