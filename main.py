import os
import subprocess
import random


import win32com.client
import xml.etree.ElementTree as ET
from xml.dom import minidom
import shutil
import time
from collections import deque


path_atual = os.path.abspath(__file__)
path_root = os.path.dirname(path_atual)
path_xml = os.path.join(path_root, "base.xml")
if os.path.isfile(path_xml):
    pass

else:
    arq = open(path_xml, "w")
    arq.write("<Root>\n</Root>")
    arq.close()

tree = ET.parse(path_xml)
root = tree.getroot()
discos_xml = [elemento.get("Nome") for elemento in root]


def add_disco(nome):
    for disco in discos:
        if disco.nome == nome:
            add_disco_xml(disco)


def add_disco_xml(disco):
    global discos_xml
    global root
    if disco.nome not in discos_xml:
        discos_xml.append(disco.nome)
        new_elem = ET.Element("Disco")
        root.append(new_elem)
        new_elem.text = "\n"
        new_elem.set("Nome", disco.nome)
        print("Disco {} adicionado.".format(disco.nome))
    
    salvar_xml(path_xml)
            


def salvar_xml(nome):
    xml_list = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ").split("\n")[1:]
    xml_string = ""
    for linha in xml_list:
        if linha != "" and linha != "  " and linha != "    ":
            xml_string += linha + "\n"

    with open(nome, "w", encoding="utf-8") as file:
        file.write(xml_string)


def select_disco(nome):
    if nome in discos_xml:
        elems = [elemento for elemento in root.findall('.//Disco') if elemento.get('Nome') == nome]
        return elems[0]
    
    else:
        raise Exception("Disco {} não encontrado.".format(nome))


def select_dirs(elem_disco):
    elems_dirs_disco = elem_disco.findall('Dir')
    tags_foto = []
    for elem in elems_dirs_disco:
        tags_foto.append(elem.text)

    return tags_foto


def add_dirs(nome, dirs_novos):
    elem = select_disco(nome)
    dirs_registrados = select_dirs(elem)
    for dir_novo in dirs_novos:
        if dir_novo not in dirs_registrados:
            new_dir = ET.Element("Dir")
            new_dir.text = dir_novo
            elem.append(new_dir)
            salvar_xml(path_xml)
            print("Diretorio {} adicionado.".format(dir_novo))


def dir(caminho="", letra=""):
    comandos = [
    letra,
    '$arqs = dir ' + caminho,
    com_sep,
    '$arqs | Select-Object Name',
    com_sep,
    '$arqs | Select-Object Mode',
    com_sep,
    '$arqs | Select-Object Length',
    com_sep
    ]

    infos_arquivos = novo_subprocess(comandos)
    return infos_arquivos


def step(files_system={}, caminho="", letra=""):
    infos_arquivos = dir(caminho, letra)
    diretorios = []
    files = []
    for arq in infos_arquivos:
        if "d" in arq[1]:
            diretorios.append(arq[0])
        
        else:
            files.append(arq[0] + "|" + arq[2])
    
    files_system[caminho] = {"diretorios": diretorios, "files": files}
    for diretorio in diretorios:
        if caminho != "":
            caminho += "\\"

        step(files_system, caminho + diretorio, letra)
    
    return files_system


def set_files_system(files_system={}, caminho="", letra=""):
    files_system = step(files_system, caminho, letra)
    return files_system


class Disco:
    def __init__(self, infos):
        self.files_system = {}
        self.letra = infos[0]
        self.nome = infos[1]
        self.tipo = infos[2]
    

    def __str__(self):
        return self.letra + "(" + self.nome + ")"
    
 
    def setar_nome(self):
        letra_aleatoria = lambda: random.choice(["a", "b", "c", "d", "e", "f", "g"])
        nome = ""
        for _ in range(6):
            nome += letra_aleatoria()
        
        self.nome = "sem_nome"


    def set_files_system(self):
        self.files_system = set_files_system(self.files_system, "", self.letra)


sep = "skip"
com_sep = "echo " + sep

def novo_subprocess(comandos):
    processo = subprocess.Popen(["powershell", "-Command", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    for comando in comandos:
        processo.stdin.write(comando + "\n")
        processo.stdin.flush()

    processo.stdin.close()

    palavras_str = ""
    saida = processo.stdout.readline()
    while saida:
        palavra = saida.strip()
        palavras_str += palavra + "\n"
        saida = processo.stdout.readline()

    if palavras_str.replace("\n", "").replace(sep, "") == "":
        return []

    colunas = palavras_str.split(sep)
    colunas_formatado = []
    for coluna in colunas:
        if len(coluna) > 5:
            coluna_temp = coluna.split("\n")[2:-3]
            coluna_temp.pop(1)
            colunas_formatado.append(coluna_temp)
    
    infos_objetos = []
    for i, _ in enumerate(colunas_formatado[0][1:]):
        caracteristicas_objeto = []
        for coluna in colunas_formatado:
            caracteristicas_objeto.append(coluna[i + 1])

        infos_objetos.append(caracteristicas_objeto)

    return infos_objetos


comandos_disks = [
'$discos = Get-WmiObject Win32_LogicalDisk',
com_sep,
'$discos | Select-Object DeviceID',
com_sep,
'$discos | Select-Object VolumeName',
com_sep,
'$discos | Select-Object DriveType',
com_sep
]

infos_discos = novo_subprocess(comandos_disks)

discos = []
for info_disco in infos_discos:
    discos.append(Disco(info_disco))

print("Discos conectados:")
for disco in discos:
    print(disco)

print()

files_system_atual = set_files_system()

discos_nao_registrados = []




for disco in discos:
    if disco.tipo == "2":
        if disco.nome in discos_xml:
            print("Disco atual:", disco.nome)
            disco.set_files_system()
            for diretorio in select_dirs(select_disco(disco.nome)):
                arquivos_fs_atual = files_system_atual[diretorio]["files"]
                arquivos_fs_disco = disco.files_system[diretorio]["files"]

                set_atual = set(arquivos_fs_atual)
                set_disco = set(arquivos_fs_disco)

                arqs_faltam_no_disco = list(set_atual - set_disco)
                arqs_excesso_no_disco = list(set_disco - set_atual)

                print("Diretorio atual:", diretorio)

                nomes_faltam_no_disco = [arq.split("|")[0] for arq in arqs_faltam_no_disco]
                nomes_excesso_no_disco = [arq.split("|")[0] for arq in arqs_excesso_no_disco]


                modificados = [nome for nome in nomes_faltam_no_disco if nome in nomes_excesso_no_disco]
                _ = [nomes_faltam_no_disco.remove(nome) for nome in modificados]
                _ = [nomes_excesso_no_disco.remove(nome) for nome in modificados]

                print("Elementos no pc e não no disco:", nomes_faltam_no_disco)
                print("Elementos no disco e não no pc:", nomes_excesso_no_disco)
                print("Elementos modificados:", modificados)

                caminhos_faltam_no_disco = [path_root + "\\" + diretorio + "\\" + nome for nome in nomes_faltam_no_disco]
                caminhos_excesso_no_disco = [disco.letra + "\\" + diretorio + "\\" + nome for nome in nomes_excesso_no_disco]
                caminhos_modificados = [path_root + "\\" + diretorio + "\\" + nome for nome in modificados]

                if len(caminhos_faltam_no_disco) > 0 or len(caminhos_excesso_no_disco) > 0 or len(caminhos_modificados) > 0:
                    escolha = input("Deseja [1] atualizar tudo, [2] somente acrescentar novos ao disco, [3] acrescentar novos e modificados ao disco ou [4] não modificar?")
                    if escolha == "1":
                        caminhos = caminhos_faltam_no_disco + caminhos_modificados
                        comandos_copy = [
                        '$destino = "D:\\abc"',
                        "$arquivos = @{}".format(str(caminhos).replace("[", "(").replace("]", ")")).replace("\\\\", "\\"),
                        """foreach ($arquivo in $arquivos) {Copy-Item -Path $arquivo -Destination $destino}""",
                        "$arquivos_del = @{}".format(str(caminhos_excesso_no_disco).replace("[", "(").replace("]", ")")).replace("\\\\", "\\"),
                        "foreach ($arquivo in $arquivos_del){Remove-Item -Path $arquivo -Force}"
                        ]

                        _ = novo_subprocess(comandos_copy)

                    elif escolha == "2":
                        caminhos = caminhos_faltam_no_disco
                        comandos_copy = [
                        '$destino = "D:\\abc"',
                        "$arquivos = @{}".format(str(caminhos).replace("[", "(").replace("]", ")")).replace("\\\\", "\\"),
                        """foreach ($arquivo in $arquivos) {Copy-Item -Path $arquivo -Destination $destino}"""
                        ]

                        _ = novo_subprocess(comandos_copy)

                    elif escolha == "3":
                        caminhos = caminhos_faltam_no_disco + caminhos_modificados
                        comandos_copy = [
                        '$destino = "D:\\abc"',
                        "$arquivos = @{}".format(str(caminhos).replace("[", "(").replace("]", ")")).replace("\\\\", "\\"),
                        """foreach ($arquivo in $arquivos) {Copy-Item -Path $arquivo -Destination $destino}"""
                        ]

                        _ = novo_subprocess(comandos_copy)
                    
                    elif escolha == "4":
                        pass

                print()
        
        else:
            discos_nao_registrados.append(disco)


if len(discos_nao_registrados) > 0:
    print("Existem discos não registrados...")
    for disco in discos_nao_registrados:
        if disco.nome != "":
            resposta = input("Deseja registrar o disco {}?[Y/N] ".format(disco.nome))
            if resposta == "Y":
                add_disco_xml([disco])









print("Comandos posteriores.")
print("Disponiveis: add_dirs(nome, dirs_novos); add_disco(nome); break")
while True:
    comandos_posteriores = input(">>> ")
    exec(comandos_posteriores)








