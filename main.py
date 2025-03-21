import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os

class LigaRecordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Liga Record PRO")
        self.root.geometry("1400x800")
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=30)
        
        self.caminho_excel = "jogadores.xlsx"
        self.carregar_dados()
        self.criar_gui()
    
    # ==================== [Funções de Dados] ====================
    def carregar_dados(self):
        """Carrega e sanitiza os dados do Excel"""
        try:
            if not os.path.exists(self.caminho_excel):
                raise FileNotFoundError("Arquivo jogadores.xlsx não encontrado!")
            
            self.df = pd.read_excel(self.caminho_excel)
            
            colunas_necessarias = ['Nome', 'Posição', 'Titular', 'Suplente', 'Reserva',
                                   'Pontos Totais', 'Pontos Última Jornada', 'Dificuldade do Jogo',
                                   'Preço', 'Lesionado', 'Expulso', 'Próximo Adversário']
            for col in colunas_necessarias:
                if col not in self.df.columns:
                    self.df[col] = False if col in ['Titular', 'Suplente', 'Reserva', 'Lesionado', 'Expulso'] else 0
            
            for col in ['Titular', 'Suplente', 'Reserva', 'Lesionado', 'Expulso']:
                self.df[col] = self.df[col].astype(bool)
            
            self.calcular_metricas()
            
        except Exception as e:
            messagebox.showerror("Erro Fatal", f"{str(e)}")
            self.root.destroy()
    
    def calcular_metricas(self):
        """Calcula scores e normaliza dados"""
        self.df['Score Ajustado'] = (
            self.df['Pontos Totais'] * 0.5 + 
            self.df['Pontos Última Jornada'] * 0.3 + 
            1/(self.df['Dificuldade do Jogo'] + 1) * 0.2
        )
        
        scaler = MinMaxScaler()
        self.df['Score Ajustado'] = scaler.fit_transform(self.df[['Score Ajustado']])
        self.df['Score Capitão'] = self.df['Score Ajustado'] * 0.7 + (1/(self.df['Dificuldade do Jogo']+1)) * 0.3

    # ==================== [Interface Gráfica] ====================
    def criar_gui(self):
        """Configura a interface gráfica principal"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        # Criar abas
        self.aba_selecao = ttk.Frame(self.notebook)
        self.aba_equipa = ttk.Frame(self.notebook)
        self.aba_taticas = ttk.Frame(self.notebook)
        self.aba_capitao = ttk.Frame(self.notebook)
        self.aba_transferencias = ttk.Frame(self.notebook)

        self.notebook.add(self.aba_selecao, text="Seleção de Equipa")
        self.notebook.add(self.aba_equipa, text="Melhor Equipa")
        self.notebook.add(self.aba_taticas, text="Táticas")
        self.notebook.add(self.aba_capitao, text="Capitão")
        self.notebook.add(self.aba_transferencias, text="Transferências")

        # Configurar cada aba
        self.criar_aba_selecao()
        self.criar_aba_equipa()
        self.criar_aba_taticas()
        self.criar_aba_capitao()
        self.criar_aba_transferencias()

    # ==================== [Aba Seleção de Equipa] ====================
    def criar_aba_selecao(self):
        """Cria a interface de seleção de jogadores"""
        frame_principal = ttk.Frame(self.aba_selecao)
        frame_principal.pack(fill='both', expand=True, padx=10, pady=10)

        # Filtros
        frame_filtros = ttk.Frame(frame_principal)
        frame_filtros.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(frame_filtros, text="Filtrar por Nome:").grid(row=0, column=0, padx=5)
        self.filtro_nome = ttk.Entry(frame_filtros)
        self.filtro_nome.grid(row=0, column=1, padx=5)
        
        ttk.Label(frame_filtros, text="Posição:").grid(row=0, column=2, padx=5)
        self.filtro_posicao = ttk.Combobox(frame_filtros, values=["", "Goleiro", "Defesa", "Médio", "Avançado"], state="readonly")
        self.filtro_posicao.grid(row=0, column=3, padx=5)
        
        ttk.Label(frame_filtros, text="Status:").grid(row=0, column=4, padx=5)
        self.filtro_status = ttk.Combobox(frame_filtros, values=["", "Titular", "Suplente", "Reserva"], state="readonly")
        self.filtro_status.grid(row=0, column=5, padx=5)
        
        ttk.Button(frame_filtros, text="Aplicar Filtros", command=self.aplicar_filtros).grid(row=0, column=6, padx=5)

        # Tabela de jogadores
        frame_tabela = ttk.Frame(frame_principal)
        frame_tabela.pack(fill='both', expand=True)
        
        colunas = ('Nome', 'Posição', 'Status')
        self.treeview = ttk.Treeview(frame_tabela, columns=colunas, show='headings', height=15)
        
        for col in colunas:
            self.treeview.heading(col, text=col)
            self.treeview.column(col, anchor='center', width=200)
        
        scrollbar = ttk.Scrollbar(frame_tabela, orient='vertical', command=self.treeview.yview)
        scrollbar.pack(side='right', fill='y')
        self.treeview.configure(yscrollcommand=scrollbar.set)
        self.treeview.pack(side='left', fill='both', expand=True)
        
        self.preencher_tabela()
        
        # Menu de contexto
        self.menu_contexto = tk.Menu(self.root, tearoff=False)
        for status in ["Titular", "Suplente", "Reserva", "Não Utilizado"]:
            self.menu_contexto.add_command(label=status, command=lambda s=status: self.mudar_status(s))
        
        self.treeview.bind("<Button-3>", self.mostrar_menu_contexto)
        
        # Botão de salvar
        ttk.Button(frame_principal, text="Salvar Alterações", command=self.salvar_alteracoes).pack(pady=10)

    def preencher_tabela(self):
        for item in self.treeview.get_children():
            self.treeview.delete(item)
        for idx, row in self.df.iterrows():
            status = 'Titular' if row['Titular'] else 'Suplente' if row['Suplente'] else 'Reserva' if row['Reserva'] else 'Não Utilizado'
            self.treeview.insert('', 'end', iid=f"{row['Nome']}_{idx}", values=(row['Nome'], row['Posição'], status))

    def mostrar_menu_contexto(self, event):
        item = self.treeview.identify_row(event.y)
        if item:
            self.treeview.selection_set(item)
            self.menu_contexto.post(event.x_root, event.y_root)

    def mudar_status(self, novo_status):
        item = self.treeview.selection()[0]
        valores = list(self.treeview.item(item, 'values'))
        valores[2] = novo_status
        self.treeview.item(item, values=valores)
        nome = valores[0]
        mask = self.df['Nome'] == nome
        self.df.loc[mask, 'Titular'] = (novo_status == 'Titular')
        self.df.loc[mask, 'Suplente'] = (novo_status == 'Suplente')
        self.df.loc[mask, 'Reserva'] = (novo_status == 'Reserva')

    def aplicar_filtros(self):
        nome = self.filtro_nome.get().lower()
        posicao = self.filtro_posicao.get()
        status = self.filtro_status.get()
        
        for item in self.treeview.get_children():
            self.treeview.delete(item)
            
        for idx, row in self.df.iterrows():
            jogador_status = 'Titular' if row['Titular'] else 'Suplente' if row['Suplente'] else 'Reserva' if row['Reserva'] else 'Não Utilizado'
            if (nome in row['Nome'].lower() or not nome) and (posicao == row['Posição'] or not posicao) and (status == jogador_status or not status):
                self.treeview.insert('', 'end', iid=f"{row['Nome']}_{idx}", values=(row['Nome'], row['Posição'], jogador_status))

    def salvar_alteracoes(self):
        try:
            self.df.to_excel(self.caminho_excel, index=False)
            messagebox.showinfo("Sucesso", "Alterações salvas com sucesso!")
            self.preencher_tabela()
            self.atualizar_melhor_equipa()
            self.comparar_taticas()
            self.sugerir_capitao()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")

    # ==================== [Aba Melhor Equipa] ====================
    def criar_aba_equipa(self):
        frame_controles = ttk.Frame(self.aba_equipa)
        frame_controles.pack(pady=10)
        
        ttk.Label(frame_controles, text="Formação Tática:").pack(side=tk.LEFT, padx=5)
        self.combo_formacao = ttk.Combobox(frame_controles, values=["4-4-2", "4-3-3", "3-5-2", "3-4-3", "4-5-1", "5-3-2"], state="readonly")
        self.combo_formacao.set("4-4-2")
        self.combo_formacao.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_controles, text="Atualizar Equipa", command=self.atualizar_melhor_equipa).pack(side=tk.LEFT)
        
        self.frame_tabela_equipa = ttk.Frame(self.aba_equipa)
        self.frame_tabela_equipa.pack(fill='both', expand=True, padx=10, pady=10)
        self.atualizar_melhor_equipa()

    def atualizar_melhor_equipa(self):
        for widget in self.frame_tabela_equipa.winfo_children():
            widget.destroy()
            
        formacao = self.combo_formacao.get()
        melhor_onze = self.selecionar_melhor_onze(formacao)
        
        colunas = ('Posição', 'Nome', 'Score Ajustado', 'Preço')
        tabela = ttk.Treeview(self.frame_tabela_equipa, columns=colunas, show='headings')
        
        for col in colunas:
            tabela.heading(col, text=col)
            tabela.column(col, anchor='center', width=150)
        
        for _, jogador in melhor_onze.iterrows():
            tabela.insert('', 'end', values=(
                jogador['Posição'],
                jogador['Nome'],
                f"{jogador['Score Ajustado']:.2f}",
                f"€{jogador['Preço']:.2f}"
            ))
        
        tabela.pack(fill='both', expand=True)

    def selecionar_melhor_onze(self, formacao):
        mapeamento = {
            "4-4-2": {'Goleiro':1, 'Defesa':4, 'Médio':4, 'Avançado':2},
            "4-3-3": {'Goleiro':1, 'Defesa':4, 'Médio':3, 'Avançado':3},
            "3-5-2": {'Goleiro':1, 'Defesa':3, 'Médio':5, 'Avançado':2},
            "3-4-3": {'Goleiro':1, 'Defesa':3, 'Médio':4, 'Avançado':3},
            "4-5-1": {'Goleiro':1, 'Defesa':4, 'Médio':5, 'Avançado':1},
            "5-3-2": {'Goleiro':1, 'Defesa':5, 'Médio':3, 'Avançado':2}
        }
        
        disponiveis = self.df[(self.df['Titular'] | self.df['Suplente'] | self.df['Reserva']) & ~self.df['Lesionado']]
        equipe = pd.DataFrame()
        
        for pos, qtd in mapeamento[formacao].items():
            jogadores_pos = disponiveis[disponiveis['Posição'] == pos].nlargest(qtd, 'Score Ajustado')
            equipe = pd.concat([equipe, jogadores_pos])
            
        return equipe

    # ==================== [Aba Táticas] ====================
    def criar_aba_taticas(self):
        frame_principal = ttk.Frame(self.aba_taticas)
        frame_principal.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(frame_principal, text="Comparação de Formações", font=("Helvetica", 16)).pack(pady=10)
        
        colunas = ('Formação', 'Pontuação Total')
        self.treeview_taticas = ttk.Treeview(frame_principal, columns=colunas, show='headings', height=10)
        
        for col in colunas:
            self.treeview_taticas.heading(col, text=col)
            self.treeview_taticas.column(col, anchor='center', width=200)
            
        self.treeview_taticas.pack(fill='both', expand=True)
        ttk.Button(frame_principal, text="Comparar Táticas", command=self.comparar_taticas).pack(pady=10)

    def comparar_taticas(self):
        formacoes = ["4-4-2", "4-3-3", "3-5-2", "3-4-3", "4-5-1", "5-3-2"]
        resultados = []
        
        for formacao in formacoes:
            melhor_onze = self.selecionar_melhor_onze(formacao)
            total = melhor_onze['Score Ajustado'].sum()
            resultados.append((formacao, total))
        
        resultados.sort(key=lambda x: x[1], reverse=True)
        
        for item in self.treeview_taticas.get_children():
            self.treeview_taticas.delete(item)
            
        for formacao, total in resultados:
            self.treeview_taticas.insert('', 'end', values=(formacao, f"{total:.2f}"))

    # ==================== [Aba Capitão] ====================
    def criar_aba_capitao(self):
        frame_principal = ttk.Frame(self.aba_capitao)
        frame_principal.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(frame_principal, text="Melhores Candidatos a Capitão", font=("Helvetica", 16)).pack(pady=10)
        
        colunas = ('Nome', 'Posição', 'Score Capitão', 'Próximo Adversário', 'Dificuldade')
        self.treeview_capitaes = ttk.Treeview(frame_principal, columns=colunas, show='headings', height=10)
        
        for col in colunas:
            self.treeview_capitaes.heading(col, text=col)
            self.treeview_capitaes.column(col, anchor='center', width=150)
            
        self.treeview_capitaes.pack(fill='both', expand=True)
        ttk.Button(frame_principal, text="Atualizar Sugestões", command=self.sugerir_capitao).pack(pady=10)

    def sugerir_capitao(self):
        for item in self.treeview_capitaes.get_children():
            self.treeview_capitaes.delete(item)
            
        titulares = self.df[self.df['Titular']].nlargest(5, 'Score Capitão')
        for _, capitao in titulares.iterrows():
            self.treeview_capitaes.insert('', 'end', values=(
                capitao['Nome'],
                capitao['Posição'],
                f"{capitao['Score Capitão']:.2f}",
                capitao['Próximo Adversário'],
                capitao['Dificuldade do Jogo']
            ))

    # ==================== [Aba Transferências] ====================
    def criar_aba_transferencias(self):
        frame_principal = ttk.Frame(self.aba_transferencias)
        frame_principal.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(frame_principal, text="Sugestões de Transferências", font=("Helvetica", 16)).pack(pady=10)
        
        frame_selecao = ttk.Frame(frame_principal)
        frame_selecao.pack(pady=10)
        
        ttk.Label(frame_selecao, text="Posição:").grid(row=0, column=0, padx=5)
        self.combo_posicao_transf = ttk.Combobox(frame_selecao, values=["Goleiro", "Defesa", "Médio", "Avançado"], state="readonly")
        self.combo_posicao_transf.set("Goleiro")
        self.combo_posicao_transf.grid(row=0, column=1, padx=5)
        
        ttk.Label(frame_selecao, text="Orçamento (€):").grid(row=0, column=2, padx=5)
        self.entrada_orcamento = ttk.Entry(frame_selecao)
        self.entrada_orcamento.grid(row=0, column=3, padx=5)
        
        ttk.Button(frame_selecao, text="Buscar Sugestões", command=self.buscar_transferencias).grid(row=0, column=4, padx=5)
        
        self.frame_sugestoes = ttk.Frame(frame_principal)
        self.frame_sugestoes.pack(fill='both', expand=True)

    def buscar_transferencias(self):
        posicao = self.combo_posicao_transf.get()
        try:
            orcamento = float(self.entrada_orcamento.get())
        except ValueError:
            messagebox.showerror("Erro", "Orçamento inválido!")
            return
        
        resultado = self.sugerir_transferencias(posicao, orcamento)
        
        for widget in self.frame_sugestoes.winfo_children():
            widget.destroy()
            
        if resultado['sugestoes']['top_performers'].empty and resultado['sugestoes']['custo_beneficio'].empty:
            ttk.Label(self.frame_sugestoes, text="Nenhuma sugestão válida encontrada.").pack()
            return
        
        # Header de informações
        frame_header = ttk.Frame(self.frame_sugestoes)
        frame_header.pack(fill='x', padx=10, pady=5)
        
        if not resultado['jogador_venda'].empty:
            jogador_venda = resultado['jogador_venda'].iloc[0]
            ttk.Label(frame_header, 
                    text=f"Sugerimos vender {jogador_venda['Nome']} (Valor: €{jogador_venda['Preço']:.2f})",
                    foreground="red").pack()
            ttk.Label(frame_header, 
                    text=f"Novo orçamento disponível: €{resultado['orcamento_ajustado']:.2f}").pack()
        
        # Cria abas para diferentes tipos de sugestões
        notebook_sugestoes = ttk.Notebook(self.frame_sugestoes)
        notebook_sugestoes.pack(fill='both', expand=True)
        
        # Tab 1 - Top Performers
        frame_top = ttk.Frame(notebook_sugestoes)
        notebook_sugestoes.add(frame_top, text="Top Performers")
        
        for i, (_, sug) in enumerate(resultado['sugestoes']['top_performers'].iterrows(), 1):
            frame_sug = ttk.Frame(frame_top, relief="groove", borderwidth=1)
            frame_sug.pack(fill='x', padx=10, pady=5)
            
            ttk.Label(frame_sug, text=f"Sugestão Premium {i}", font=("Helvetica", 12, "bold")).pack()
            ttk.Label(frame_sug, text=f"Jogador: {sug['Nome']}").pack()
            ttk.Label(frame_sug, text=f"Preço: €{sug['Preço']:.2f} | Score: {sug['Score Avançado']:.2f}").pack()
            ttk.Label(frame_sug, text=f"Próximo Jogo: {sug['Próximo Adversário']} (Dificuldade: {sug['Dificuldade do Jogo']}/5)").pack()
        
        # Tab 2 - Custo-Benefício
        frame_custo = ttk.Frame(notebook_sugestoes)
        notebook_sugestoes.add(frame_custo, text="Melhor Custo-Benefício")
        
        for i, (_, sug) in enumerate(resultado['sugestoes']['custo_beneficio'].iterrows(), 1):
            frame_sug = ttk.Frame(frame_custo, relief="groove", borderwidth=1)
            frame_sug.pack(fill='x', padx=10, pady=5)
            
            ttk.Label(frame_sug, text=f"Sugestão Econômica {i}", font=("Helvetica", 12, "bold")).pack()
            ttk.Label(frame_sug, text=f"Jogador: {sug['Nome']}").pack()
            ttk.Label(frame_sug, text=f"Preço: €{sug['Preço']:.2f} | Score: {sug['Score Avançado']:.2f}").pack()

    def sugerir_transferencias(self, posicao, orcamento):
        """Sugere transferências com comparação de jogadores e gestão de orçamento dinâmico"""
        # Identificar jogadores atuais na posição
        jogadores_atuais = self.df[
            (self.df['Posição'] == posicao) & 
            (self.df['Titular'] | self.df['Suplente'] | self.df['Reserva'])
        ]
        
        # Encontrar o jogador mais substituível
        jogador_substituivel = jogadores_atuais.nsmallest(1, 'Score Ajustado')
        bonus_venda = jogador_substituivel['Preço'].values[0] if not jogador_substituivel.empty else 0
        orcamento_total = orcamento + bonus_venda
        
        # Fatores de ponderação
        peso_recente = 0.4
        peso_dificuldade = 0.3
        
        # Calcular score aprimorado
        df_filtrado = self.df[
            (self.df['Posição'] == posicao) &
            (~self.df['Titular']) &
            (self.df['Preço'] <= orcamento_total)
        ].copy()
        
        df_filtrado['Score Avançado'] = (
            df_filtrado['Pontos Última Jornada'] * peso_recente +
            (1 / (df_filtrado['Dificuldade do Jogo'] + 1)) * peso_dificuldade +
            df_filtrado['Score Ajustado'] * (1 - peso_recente - peso_dificuldade)
        )
        
        # Comparar com jogadores atuais
        if not jogadores_atuais.empty:
            score_minimo = jogadores_atuais['Score Ajustado'].min() * 1.2
            df_filtrado = df_filtrado[df_filtrado['Score Avançado'] > score_minimo]
        
        # Gerar sugestões estratificadas
        sugestoes = {
            'top_performers': df_filtrado.nlargest(3, 'Score Avançado'),
            'custo_beneficio': df_filtrado[df_filtrado['Preço'] <= orcamento].nlargest(3, 'Score Avançado')
        }
        
        return {
            'sugestoes': sugestoes,
            'jogador_venda': jogador_substituivel,
            'orcamento_ajustado': orcamento_total
        }

if __name__ == "__main__":
    root = tk.Tk()
    app = LigaRecordApp(root)
    root.mainloop()
