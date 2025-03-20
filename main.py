import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# Configuração inicial
class LigaRecordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Liga Record PRO")
        self.root.geometry("1200x800")
        
        # Carregar dados
        try:
            self.df = self.carregar_dados("jogadores.xlsx")
            self.df = self.calcular_metricas()
            self.equipe_atual = self.obter_equipe_atual()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar dados: {str(e)}")
            self.root.destroy()
            return
        
        # Configurar interface
        self.criar_gui()
    
    def carregar_dados(self, caminho):
        """Carrega dados do Excel com tratamento de tipos"""
        df = pd.read_excel(caminho, dtype={
            'Lesionado': str, 'Expulso': str,
            'Titular': str, 'Suplente': str, 'Reserva': str
        })
        
        # Conversão para booleanos
        bool_map = {'true': True, 'false': False, '1': True, '0': False,
                   'sim': True, 'não': False, 'yes': True, 'no': False}
        for col in ['Lesionado', 'Expulso', 'Titular', 'Suplente', 'Reserva']:
            df[col] = df[col].str.strip().str.lower().map(bool_map).fillna(False)
        
        return df

    def calcular_metricas(self):
        """Calcula as métricas dos jogadores"""
        df = self.df.copy()
        df['Score Ajustado'] = (df['Pontos Totais'] * 0.5 + 
                               df['Pontos Última Jornada'] * 0.3 + 
                               1/(df['Dificuldade do Jogo']+1) * 0.2)
        
        scaler = MinMaxScaler()
        df['Score Ajustado'] = scaler.fit_transform(df[['Score Ajustado']])
        df['Score Capitão'] = df['Score Ajustado'] * 0.7 + (1/(df['Dificuldade do Jogo']+1)) * 0.3
        return df

    def obter_equipe_atual(self):
        """Filtra a equipe atual do usuário"""
        return self.df[self.df['Titular'] | self.df['Suplente'] | self.df['Reserva']]

# Digite "continuar" para receber a Parte 2/4
    def criar_gui(self):
        """Configura a interface gráfica principal com abas"""
        # Título principal
        titulo = ttk.Label(self.root, text="Liga Record PRO", font=("Helvetica", 24))
        titulo.pack(pady=10)
        
        # Notebook (abas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        
        # Criar as abas
        self.aba_equipa = ttk.Frame(self.notebook)
        self.aba_taticas = ttk.Frame(self.notebook)
        self.aba_capitao = ttk.Frame(self.notebook)
        self.aba_transferencias = ttk.Frame(self.notebook)
        
        self.notebook.add(self.aba_equipa, text="Melhor Equipa")
        self.notebook.add(self.aba_taticas, text="Táticas")
        self.notebook.add(self.aba_capitao, text="Capitão")
        self.notebook.add(self.aba_transferencias, text="Transferências")
        
        # Exibir conteúdo inicial em cada aba
        self.exibir_melhor_equipa()
        self.exibir_taticas()
        self.exibir_capitao()
        self.exibir_transferencias()

    # =================================================================
    # FUNÇÕES PARA EXIBIR CONTEÚDO EM CADA ABA
    # =================================================================

    def exibir_melhor_equipa(self):
        """Exibe a melhor equipe na aba 'Melhor Equipa'"""
        for widget in self.aba_equipa.winfo_children():
            widget.destroy()
        
        titulo = ttk.Label(self.aba_equipa, text="Melhor Equipa Selecionada", font=("Helvetica", 18))
        titulo.pack(pady=10)
        
        # Tabela para exibir os jogadores
        colunas = ("Nome", "Posição", "Score Ajustado", "Preço")
        tabela = ttk.Treeview(self.aba_equipa, columns=colunas, show="headings")
        
        for col in colunas:
            tabela.heading(col, text=col)
            tabela.column(col, anchor="center", width=200)
        
        melhor_onze = self.selecionar_melhor_onze("4-4-2")  # Exemplo de formação padrão
        for _, jogador in melhor_onze.iterrows():
            tabela.insert("", tk.END, values=(jogador['Nome'], jogador['Posição'], f"{jogador['Score Ajustado']:.2f}", jogador['Preço']))
        
        tabela.pack(fill="both", expand=True)

    def exibir_taticas(self):
        """Exibe as melhores táticas sugeridas na aba 'Táticas'"""
        for widget in self.aba_taticas.winfo_children():
            widget.destroy()
        
        titulo = ttk.Label(self.aba_taticas, text="Melhores Táticas Sugeridas", font=("Helvetica", 18))
        titulo.pack(pady=10)
        
        melhores_taticas = self.comparar_taticas()
        
        for i, (tatica, score, requisitos) in enumerate(melhores_taticas, 1):
            texto = f"{i}. {tatica} - Score Total: {score:.2f}"
            detalhes = f"Defesa: {requisitos['Defesa']}, Médio: {requisitos['Médio']}, Avançado: {requisitos['Avançado']}"
            
            label_tatica = ttk.Label(self.aba_taticas, text=f"{texto}\n{detalhes}", font=("Helvetica", 14))
            label_tatica.pack(pady=5)

# Digite "continuar" para receber a Parte 3/4 com as funções de Capitão e Transferências.
    def exibir_capitao(self):
        """Exibe os melhores candidatos a capitão na aba 'Capitão'"""
        for widget in self.aba_capitao.winfo_children():
            widget.destroy()
        
        titulo = ttk.Label(self.aba_capitao, text="Melhores Candidatos a Capitão", font=("Helvetica", 18))
        titulo.pack(pady=10)
        
        capitaes = self.sugerir_capitao()
        
        # Tabela para exibir os candidatos a capitão
        colunas = ("Nome", "Posição", "Score Capitão", "Próximo Adversário", "Dificuldade")
        tabela = ttk.Treeview(self.aba_capitao, columns=colunas, show="headings")
        
        for col in colunas:
            tabela.heading(col, text=col)
            tabela.column(col, anchor="center", width=150)
        
        for _, capitao in capitaes.iterrows():
            tabela.insert("", tk.END, values=(
                capitao['Nome'],
                capitao['Posição'],
                f"{capitao['Score Capitão']:.2f}",
                capitao['Próximo Adversário'],
                capitao['Dificuldade do Jogo']
            ))
        
        tabela.pack(fill="both", expand=True)

    def exibir_transferencias(self):
        """Configura a aba de Transferências"""
        for widget in self.aba_transferencias.winfo_children():
            widget.destroy()
        
        titulo = ttk.Label(self.aba_transferencias, text="Sugestões de Transferências", font=("Helvetica", 18))
        titulo.pack(pady=10)
        
        # Frame para seleção de posição e orçamento
        frame_selecao = ttk.Frame(self.aba_transferencias)
        frame_selecao.pack(pady=10)
        
        ttk.Label(frame_selecao, text="Posição:").grid(row=0, column=0, padx=5)
        self.combo_posicao = ttk.Combobox(frame_selecao, values=["Goleiro", "Defesa", "Médio", "Avançado"])
        self.combo_posicao.grid(row=0, column=1, padx=5)
        self.combo_posicao.set("Goleiro")
        
        ttk.Label(frame_selecao, text="Orçamento (€):").grid(row=0, column=2, padx=5)
        self.entrada_orcamento = ttk.Entry(frame_selecao)
        self.entrada_orcamento.grid(row=0, column=3, padx=5)
        
        ttk.Button(frame_selecao, text="Buscar Sugestões", command=self.buscar_transferencias).grid(row=0, column=4, padx=5)
        
        # Frame para exibir as sugestões
        self.frame_sugestoes = ttk.Frame(self.aba_transferencias)
        self.frame_sugestoes.pack(fill="both", expand=True)

    def buscar_transferencias(self):
        """Busca e exibe sugestões de transferências"""
        posicao = self.combo_posicao.get()
        try:
            orcamento = float(self.entrada_orcamento.get())
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um valor numérico válido para o orçamento.")
            return
        
        sugestoes = self.sugerir_transferencias(posicao, orcamento)
        
        # Limpar sugestões anteriores
        for widget in self.frame_sugestoes.winfo_children():
            widget.destroy()
        
        if not sugestoes:
            ttk.Label(self.frame_sugestoes, text="Nenhuma sugestão encontrada.").pack()
            return
        
        # Exibir novas sugestões
        for i, sug in enumerate(sugestoes, 1):
            frame_sug = ttk.Frame(self.frame_sugestoes, relief="raised", borderwidth=1)
            frame_sug.pack(fill="x", padx=10, pady=5)
            
            ttk.Label(frame_sug, text=f"Sugestão {i}", font=("Helvetica", 12, "bold")).pack()
            ttk.Label(frame_sug, text=f"Ação: {sug['Ação']}").pack()
            ttk.Label(frame_sug, text=f"Custo: €{sug['Custo Total']:.2f}").pack()
            ttk.Label(frame_sug, text=f"Ganho de Score: {sug['Ganho Score']:.2f}").pack()

# Digite "continuar" para receber a Parte 4/4 com as funções de lógica de negócio e inicialização do programa.
    # =================================================================
    # FUNÇÕES DE LÓGICA DE NEGÓCIO
    # =================================================================

    def selecionar_melhor_onze(self, tatica):
        """Seleciona o melhor onze baseado na tática escolhida"""
        formacoes = {
            "3-4-3": (3,4,3), "3-5-2": (3,5,2), "4-3-3": (4,3,3),
            "4-4-2": (4,4,2), "4-5-1": (4,5,1), "5-3-2": (5,3,2), "5-4-1": (5,4,1)
        }
        defesa, meio, ataque = formacoes.get(tatica, (4,4,2))
        
        disponiveis = self.equipe_atual[~self.equipe_atual['Lesionado'] & ~self.equipe_atual['Expulso']]
        
        gr = disponiveis[disponiveis['Posição'] == 'Goleiro'].nlargest(1, 'Score Ajustado')
        defesas = disponiveis[disponiveis['Posição'] == 'Defesa'].nlargest(defesa, 'Score Ajustado')
        medios = disponiveis[disponiveis['Posição'] == 'Médio'].nlargest(meio, 'Score Ajustado')
        avancados = disponiveis[disponiveis['Posição'] == 'Avançado'].nlargest(ataque, 'Score Ajustado')
        
        return pd.concat([gr, defesas, medios, avancados])

    def comparar_taticas(self):
        """Compara diferentes formações e sugere as melhores"""
        formacoes = {
            "3-4-3": {'Defesa': 3, 'Médio': 4, 'Avançado': 3},
            "3-5-2": {'Defesa': 3, 'Médio': 5, 'Avançado': 2},
            "4-3-3": {'Defesa': 4, 'Médio': 3, 'Avançado': 3},
            "4-4-2": {'Defesa': 4, 'Médio': 4, 'Avançado': 2},
            "4-5-1": {'Defesa': 4, 'Médio': 5, 'Avançado': 1},
            "5-3-2": {'Defesa': 5, 'Médio': 3, 'Avançado': 2},
            "5-4-1": {'Defesa': 5, 'Médio': 4, 'Avançado': 1}
        }
        
        resultados = []
        for nome, requisitos in formacoes.items():
            score_total = sum(
                self.equipe_atual[self.equipe_atual['Posição'] == pos].nlargest(qtd, 'Score Ajustado')['Score Ajustado'].sum()
                for pos, qtd in requisitos.items()
            )
            resultados.append((nome, score_total, requisitos))
        
        return sorted(resultados, key=lambda x: x[1], reverse=True)[:3]

    def sugerir_capitao(self):
        """Sugere os melhores candidatos a capitão"""
        return self.equipe_atual[self.equipe_atual['Titular']].nlargest(5, 'Score Capitão')

    def sugerir_transferencias(self, posicao_alvo, orcamento):
        """Sugere transferências para uma posição específica"""
        jogadores_pos = self.equipe_atual[self.equipe_atual['Posição'] == posicao_alvo]
        disponiveis = self.df[
            (~self.df['Nome'].isin(self.equipe_atual['Nome'])) &
            (self.df['Posição'] == posicao_alvo) &
            ~self.df['Lesionado'] &
            ~self.df['Expulso']
        ].sort_values('Score Ajustado', ascending=False)
        
        sugestoes = []
        for _, candidato in disponiveis.iterrows():
            if len(sugestoes) >= 3:
                break
            
            if not jogadores_pos.empty:
                substituto = jogadores_pos.nsmallest(1, 'Score Ajustado').iloc[0]
                novo_orcamento = orcamento + substituto['Preço']
                
                if candidato['Preço'] <= novo_orcamento:
                    sugestoes.append({
                        'Ação': f"Substituir {substituto['Nome']} por {candidato['Nome']}",
                        'Custo Total': candidato['Preço'],
                        'Ganho Score': candidato['Score Ajustado'] - substituto['Score Ajustado']
                    })
            elif candidato['Preço'] <= orcamento:
                sugestoes.append({
                    'Ação': f"Contratar {candidato['Nome']}",
                    'Custo Total': candidato['Preço'],
                    'Ganho Score': candidato['Score Ajustado']
                })
        
        return sugestoes

# Inicialização do programa
if __name__ == "__main__":
    root = tk.Tk()
    app = LigaRecordApp(root)
    root.mainloop()
