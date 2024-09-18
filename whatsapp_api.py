
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import csv
import os
import glob
from time import time
import requests

        
# Parameters
WP_LINK = 'https://web.whatsapp.com'

CONTACTS = '//*[@id="main"]/header/div[2]/div[2]/span'
MESSAGE_BOX = '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[1]'
SEND = '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[2]/button'
NEW_CHAT = '//*[@id="app"]/div/div[2]/div[3]/header/header/div/span/div/span/div[1]/div/span'
FIRST_CONTACT = '//*[@id="app"]/div/div[2]/div[2]/div[1]/span/div/span/div/div[2]/div/div/div/div[2]/div/div/div[2]'
SEARCH_CONTACT = '//*[@id="app"]/div/div[2]/div[2]/div[1]/span/div/span/div/div[1]/div[2]/div[2]/div/div[1]'
NEW_MESSAGE_INDICATOR = './/span[contains(@class, "_2_LEW") or contains(@class, "_1pJ9J")]'
SIDEBAR_CONTACTS_XPATH = '//*[@id="pane-side"]/div[2]/div/div'

class WhatsApp:
    def __init__(self):
        self.driver = None
        try:
            self.driver = self._setup_driver()
            self.driver.get(WP_LINK)
            print("Please scan the QR Code")
            sleep(15)  
        except Exception as e:
            print(f"Error during initialization: {e}")
            if self.driver:
                self.driver.quit()

    @staticmethod
    def _setup_driver():
        print('Loading...')
        chrome_options = Options()
        chrome_options.add_argument("disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver_path = ChromeDriverManager().install()
        print(driver_path)
        service = Service(driver_path)

        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            return driver
        except Exception as e:
            print(f"Error setting up driver: {e}")
            return None

    def _get_element(self, xpath, attempts=5, _count=0):
        '''Safe get_element method with multiple attempts'''
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element
        except Exception as e:
            if _count < attempts:
                sleep(1)
                return self._get_element(xpath, attempts=attempts, _count=_count + 1)
            else:
                print(f"Element not found: {xpath}")
                return None


    def _click(self, xpath):
        el = self._get_element(xpath)
        if el:
            el.click()
            sleep(2)

    def _send_keys(self, xpath, message):
        el = self._get_element(xpath)
        if el:
            el.send_keys(message)

    def line_break(self):
        el = self._get_element(MESSAGE_BOX)
        if el:
            el.send_keys(Keys.SHIFT, Keys.ENTER)

    def write_message(self, message):
        '''Write message in the text box but not send it'''
        self._send_keys(MESSAGE_BOX, message)

    def _paste(self):
        el = self._get_element(MESSAGE_BOX)
        if el:
            el.send_keys(Keys.SHIFT, Keys.INSERT)

    def send_message(self, message):
        '''Write and send message'''
        self.write_message(message)
        self._click(SEND)

    def get_group_numbers(self):
        '''Get phone numbers from a WhatsApp group'''
        el = self._get_element(CONTACTS)
        if el:
            return el.text.split(',')   
        print("Group header not found")
        return []

    def search_contact(self, keyword):
        '''Search and select a contact'''
        self._click(NEW_CHAT)
        self._send_keys(SEARCH_CONTACT, keyword)
        sleep(1)
        self._click(FIRST_CONTACT)

    def get_all_messages(self):
        all_messages_element = self.driver.find_elements(By.CLASS_NAME, '_akbu')
        all_messages_text = [e.text for e in all_messages_element if e.text.strip()]
        return all_messages_text

    def get_last_message(self):
        all_messages = self.get_all_messages()
        return all_messages[-1] if all_messages else None

    def check_for_new_messages(self, contact):

        last_message = self.get_last_message()
        if contact in self.last_messages:
            if last_message != self.last_messages[contact]:
                self.last_messages[contact] = last_message
                return last_message
        else:
            self.last_messages[contact] = last_message
        return None

    def monitor_chats(self, contacts, interval=10, sendmessage=''):
        while True:
            for contact in contacts:
                new_message = self.check_for_new_messages(contact)
                if new_message:
                    print(f"New message from {contact}: {new_message}")
                    self.search_contact(f'{contact}')
                    self.send_message(f'{sendmessage}')
            sleep(interval)

    def get_xpath(self, element):
        components = []
        child = element
        while child.tag_name != 'html':
            parent = child.find_element(By.XPATH, '..')
            children = parent.find_elements(By.XPATH, './*')
            index = 1
            for i in range(len(children)):
                if children[i] == child:
                    index = i + 1
                    break
            components.append(child.tag_name + '[' + str(index) + ']')
            child = parent
        components.reverse()
        return '/' + '/'.join(components)
    
    
    def click_contact(self):

        sidebar_contacts = self.driver.find_elements(By.XPATH, SIDEBAR_CONTACTS_XPATH + '/div/div/div')
        print(sidebar_contacts)
        for contact in sidebar_contacts:
            contact_text = contact.text if contact.text else ''

            if "Suas mensagens pessoais são protegidas com a criptografia de ponta a ponta" in contact_text or not contact_text:
                continue  


            contact_name = contact_text.split('\n')[0]

            print('Interacting with contact:', contact_name)
            try:
                if contact.find_elements(By.CLASS_NAME, '_ahlk'):
                    contact.click()
                    sleep(1)
                    
                    self.send_message('> teste de chatbot')  
            except Exception as e:
                print(f"Error interacting with contact {contact_name}")


    def append_analysed_contacts(self, contact_id):
        filepath = "C:\\Users\\desen\\myenv\\analysed_contacts.csv"
        with open('analysed_contacts.csv', mode='a', newline='', encoding='utf8') as file:
            file.write(contact_id)

    def create_csv(self, contact_id, time_limit_seconds=800):
        filename = f"{contact_id}.csv"
        file_path = f"C:\\Users\\desen\\myenv\\{filename}"

        self.append_analysed_contacts([contact_id])
        with open(filename, mode='a', newline='', encoding='utf8') as file:
            pass
        if os.path.exists(file_path):
            file_mod_time = os.path.getmtime(file_path)

            current_time = time()

            time_difference = current_time - file_mod_time

            if time_difference > time_limit_seconds:
                os.remove(file_path)
        
    def delete_csv(self):
        csv_files = glob.glob("*.csv")
        for file in csv_files:
            try:
                os.remove(file)
            except: 
                print('erro ao deletar arquivo.')




    def main(self):
        new_message = False
        self.last_messages = {}

        def voltar_menu(contact):
            with open(f'{contact}.csv', mode='r+', encoding='utf8') as file:
                lines = file.readlines()

                if lines:  
                    lines.pop(-1)
                    lines.pop(-1)

                file.seek(0)
                file.truncate()

                file.writelines(f"{line.strip()}\n" for line in lines)

            
        def read_menu(menu_list, index):
            if index < 0 or index >= len(menu_list):
                return 'index out of range'
            else:
                list = menu_list[index]
                lines = list.split('\n')
                for line in lines:
                    self.write_message(line)
                    self.line_break()
                
            
        def firstDialog(contact_name, file):
            print('interacting with contact: ', contact_name)
            try:
                replacements = {
                    '<name>': f'{contact_name}',
                    '<date>': '2024-09-02',
                    '<time>': '10:00'
                }

                with open(file, mode='r', encoding='utf8') as file:
                    content = file.read()
                    lines = content.split('\n')
                    for line in lines:
                        for key, value in replacements.items():
                            line = line.replace(key, value)
                        self.write_message(line)
                        self.line_break()


                        
                    self._click(SEND)

                    
                    print('success')
    
            except Exception as e:
                print('Error interacting with contact: ', contact_name)


        neutral_contact = '//*[@id="pane-side"]/div[2]/div/div/div[11]/div/div/div/div[2]'
        while True:         
            already = False
            sidebar_contacts = self.driver.find_elements(By.XPATH, SIDEBAR_CONTACTS_XPATH + '/div/div/div')

            for contact in sidebar_contacts:
                while not new_message:
                    try:
                        contact_text = contact.text.replace(' ', '-') if contact.text else ''
                    except Exception as e:
                        print('erro')
                    try:
                        if "Suas mensagens pessoais são protegidas com a criptografia de ponta a ponta" in contact_text or not contact_text:
                            continue  
                        contact_name = contact_text.split('\n')[0]

                        try:
                            
                            if contact.find_elements(By.CLASS_NAME, '_ahlk'):
                                contact.click()



                                file_path = "C:\\Users\\desen\\myenv\\analysed_contacts.csv"
                                
                                if not os.path.exists(file_path):
                                    with open(file_path, 'a'):
                                        pass


                                with open(file_path, mode='r', encoding='utf8') as file:
                                    contacts = file.readlines()
                                    analysed_contacts = [row.strip() for row in contacts]

                        
                                    if contact_name not in analysed_contacts:
                                        firstDialog(contact_name, 'menu_personalizado.txt')
                                        self.append_analysed_contacts(contact_name)
                                    
                                    else:
                                        try:

                                            menu_matrix = [
                                                ['Consulta de Saldo Concluida.', 'Histórico de Transações concluido.', 'Pagamento de faturas concluido.', 'Voltar'],
                                                ['Abrir chamado concluido.', 'Consultar Status de Chamado concluido.', 'Contato com Atendente concluido.', 'Voltar'],
                                                ['Acessando repositório concluido.', 'Criando novo projeto concluido.', 'Fazendo deploy de aplicação concluido.', 'Voltar']
                                            ]

                                            main_menu = [
                                                '1 - Consulta de Saldo\n2 - Histórico de Transações\n3 - Pagamento de Faturas\n4 - Voltar ',
                                                '1 - Abrir Chamado\n2 - Consultar Status de Chamado\n3 - Contato com Atendente\n4 - Voltar',
                                                '1 - Acessar Repositório de Código\n2 - Criar Novo Projeto\n3 - Deploy de Aplicação\n4 - Voltar'
                                                ]
                                            
                                            with open(f'{contact_name}.csv', mode='a+') as file:
                                                file.write(f'{self.get_last_message()}\n')
                                                file.seek(0)
                                                already=True
                                                content = file.readlines()
                                                lines = [line.strip() for line in content]
                                                print(lines)
                                                
                                
                                                if len(content) == 1:
                                                    try:
                                                        first_option = int(lines[0]) - 1

                                                        if 0 <= first_option < len(main_menu):
                                                            read_menu(main_menu, first_option)
                                                            self._click(SEND)
                                                        else:
                                                            self.send_message('Opção inválida. Por favor, tente novamente')
                                                            voltar_menu(contact_name)
                                                    except:
                                                        self.send_message('Opção inválida. Por favor, tente novamente')
                                                        voltar_menu(contact_name)
                    
                                                elif len(content) == 2:
                                                    try:
                                                        first_option = int(lines[0]) - 1
                                                        second_option = int(lines[1]) - 1
                                                        if 0 <= first_option < len(menu_matrix) and 0 <= second_option < len(menu_matrix[first_option]):
                                                            if second_option == 3:
                                                                voltar_menu(contact_name)
                                                                firstDialog(contact_name, 'menu_personalizado.txt')
                                                            else:
                                                                self.send_message(menu_matrix[first_option][second_option])
                                                        else:
                                                            self.send_message('Opção inválida. Por favor, tente novamente')
                                                            voltar_menu(contact_name)
                                                    except: 
                                                        self.send_message('Opção inválida. Por favor, tente novamente')
                                                        voltar_menu(contact_name)
                                                

                                        except Exception as e:
                                            print('erro arquivo 2: ', e)
                        except:
                            print('erro _ahlk eu acho')
                    except Exception as e:
                            print(e)   



if __name__ == "__main__":
    wp = WhatsApp()
    wp.delete_csv()


    wp.main()
