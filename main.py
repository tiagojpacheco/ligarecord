import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# =================================================================
# PARTE 1/3 - FUNÇÕES DE CARGA DE DADOS E PRÉ-PROCESSAMENTO
# =================================================================

def carregar_dados(caminho):
    """
    Carrega dados do Excel e realiza sanitização básica
    - Converte colunas booleanas (Lesionado, Expulso, Titular, etc)
    - Converte colunas numéricas (Preço, Pontuações)
    - Valida estrutura básica do arquivo
    """
    try:
        # Carregar mantendo dados brutos para conversão controlada
        df = pd.read_excel(caminho, dtype={
            'Lesionado': str, 'Expulso': str,
            'Titular': str, 'Suplente': str, 'Reserva': str
        })
        
        # Mapeamento robusto para valores booleanos
        bool_map = {
            'true': True, 'false': False, '1': True, '0': False,
            'sim': True, 'não': False, 'yes': True, 'no': False
        }
        
        # Aplicar conversão para colunas booleanas
        for col in ['Lesionado', 'Expulso', 'Titular', 'Suplente', 'Reserva']:
            df[col] = df[col].str.strip().str.lower().map(bool_map).fillna(False)
        
        # Converter colunas numéricas e tratar valores inválidos
        cols_numericas = ['Preço', 'Pontos Última Jornada', 'Pontos Totais', 'Dificuldade do Jogo']
        df[cols_numericas] = df[cols_numericas].apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Validação final da estrutura
        colunas_obrigatorias = ['Nome', 'Posição', 'Equipa'] + cols_numericas
        if not all(col in df.columns for col in colunas_obrigatorias):
            raise ValueError("Arquivo incompleto! Verifique as colunas.")
        
        return df
    except Exception as e:
        print(f"ERRO NA CARGA DE DADOS: {str(e)}")
        exit()

def calcular_metricas(df):
    """
    Calcula métricas avançadas para análise:
    - Score Ajustado: Combina desempenho histórico e dificuldade do próximo jogo
    - Valor/Euro: Relação entre pontuação potencial e custo do jogador
    """
    try:
        # Cálculo do Score Ajustado (50% histórico, 30% recente, 20% dificuldade)
        df['Score Ajustado'] = (
            (df['Pontos Totais'] * 0.5) + 
            (df['Pontos Última Jornada'] * 0.3) + 
            (1 / (df['Dificuldade do Jogo'] + 1) * 0.2)
        )
        
        # Normalização para escala 0-1
        scaler = MinMaxScaler()
        df['Score Ajustado'] = scaler.fit_transform(df[['Score Ajustado']])
        
        # Cálculo de valor por euro (protegido contra divisão por zero)
        df['Valor/Euro'] = df['Score Ajustado'] / df['Preço'].replace(0, 0.01)
        
        # Score para capitania (60% score ajustado, 40% dificuldade)
        df['Score Capitão'] = (df['Score Ajustado'] * 0.6) + (1 / (df['Dificuldade do Jogo'] + 1) * 0.4)
        
        return df
    except Exception as e:
        print(f"ERRO NOS CÁLCULOS: {str(e)}")
        exit()
# =================================================================
# PARTE 2/3 - FUNÇÕES DE ANÁLISE TÁTICA E SELEÇÃO DE JOGADORES
# =================================================================

def obter_equipe_atual(df):
    """
    Filtra a equipe atual do usuário
    - Considera jogadores marcados como Titular, Suplente ou Reserva
    - Verifica se há Goleiro na equipe
    """
    try:
        mascara = df['Titular'] | df['Suplente'] | df['Reserva']
        equipe = df[mascara].copy()
        
        if equipe.empty:
            raise ValueError("Nenhum jogador selecionado na equipe!")
            
        if equipe[equipe['Posição'] == 'Goleiro'].empty:
            print("ALERTA: Nenhum Goleiro na equipe!")
            
        return equipe
    except Exception as e:
        print(f"ERRO NA SELEÇÃO DA EQUIPE: {str(e)}")
        exit()

def selecionar_melhor_onze(equipe, tatica):
    """
    Seleciona a melhor formação tática baseada no Score Ajustado
    - Respeita a formação escolhida
    - Considera apenas jogadores não lesionados e não expulsos
    """
    formacoes = {
        "3-4-3": (3,4,3), "3-5-2": (3,5,2), 
        "4-3-3": (4,3,3), "4-4-2": (4,4,2),
        "4-5-1": (4,5,1), "5-3-2": (5,3,2), 
        "5-4-1": (5,4,1)
    }
    
    try:
        defesa, meio, ataque = formacoes.get(tatica, (4,4,2))
        
        # Filtrar jogadores disponíveis
        disponiveis = equipe[~equipe['Lesionado'] & ~equipe['Expulso']]
        
        # Selecionar por posição
        gr = disponiveis[disponiveis['Posição'] == 'Goleiro'].nlargest(1, 'Score Ajustado')
        defesas = disponiveis[disponiveis['Posição'] == 'Defesa'].nlargest(defesa, 'Score Ajustado')
        medios = disponiveis[disponiveis['Posição'] == 'Médio'].nlargest(meio, 'Score Ajustado')
        avancados = disponiveis[disponiveis['Posição'] == 'Avançado'].nlargest(ataque, 'Score Ajustado')
        
        return pd.concat([gr, defesas, medios, avancados])
    except Exception as e:
        print(f"ERRO NA SELEÇÃO DA FORMAÇÃO: {str(e)}")
        return pd.DataFrame()

def sugerir_substitutos(equipe):
    """
    Sugere até 3 substitutos por posição da equipe atual
    - Considera apenas jogadores marcados como Suplente ou Reserva
    - Exclui jogadores lesionados ou expulsos
    """
    try:
        substitutos = {}
        
        # Filtrar jogadores disponíveis para substituição
        disponiveis = equipe[
            (equipe['Suplente'] | equipe['Reserva']) &
            ~equipe['Lesionado'] & 
            ~equipe['Expulso']
        ]
        
        for pos in ['Goleiro', 'Defesa', 'Médio', 'Avançado']:
            subs = disponiveis[disponiveis['Posição'] == pos].nlargest(3, 'Score Ajustado')
            substitutos[pos] = subs[['Nome', 'Score Ajustado', 'Preço']].to_dict('records')
            
        return substitutos
    except Exception as e:
        print(f"ERRO NA SUGESTÃO DE SUBSTITUTOS: {str(e)}")
        return {}

def comparar_taticas(equipe):
    """
    Compara diferentes formações táticas e sugere as melhores
    - Avalia todas as formações possíveis
    - Calcula o score total para cada formação
    - Retorna as 3 melhores formações
    """
    formacoes = {
        "3-4-3": {'Defesa': 3, 'Médio': 4, 'Avançado': 3},
        "3-5-2": {'Defesa': 3, 'Médio': 5, 'Avançado': 2},
        "4-3-3": {'Defesa': 4, 'Médio': 3, 'Avançado': 3},
        "4-4-2": {'Defesa': 4, 'Médio': 4, 'Avançado': 2},
        "4-5-1": {'Defesa': 4, 'Médio': 5, 'Avançado': 1},
        "5-3-2": {'Defesa': 5, 'Médio': 3, 'Avançado': 2},
        "5-4-1": {'Defesa': 5, 'Médio': 4, 'Avançado': 1}
    }
    
    try:
        resultados = []
        for nome, requisitos in formacoes.items():
            score_total = 0
            for posicao, quantidade in requisitos.items():
                jogadores = equipe[equipe['Posição'] == posicao].nlargest(quantidade, 'Score Ajustado')
                score_total += jogadores['Score Ajustado'].sum()
            
            resultados.append((nome, score_total, requisitos))
        
        return sorted(resultados, key=lambda x: x[1], reverse=True)[:3]
    except Exception as e:
        print(f"ERRO NA COMPARAÇÃO DE TÁTICAS: {str(e)}")
        return []

def sugerir_capitao(equipe):
    """
    Sugere os melhores candidatos a capitão
    - Baseado no Score Capitão
    - Considera apenas jogadores titulares
    """
    try:
        candidatos = equipe[equipe['Titular']].nlargest(5, 'Score Capitão')
        return candidatos[['Nome', 'Posição', 'Score Capitão', 'Próximo Adversário', 'Dificuldade do Jogo']]
    except Exception as e:
        print(f"ERRO NA SUGESTÃO DE CAPITÃO: {str(e)}")
        return pd.DataFrame()
# =================================================================
# PARTE 3/3 - FUNÇÕES DE TRANSFERÊNCIA E INTERFACE DO USUÁRIO
# =================================================================

def sugerir_transferencias(df, equipe_atual, orcamento, posicao_alvo):
    """
    Sugere transferências para uma posição específica
    - Considera o orçamento disponível
    - Calcula o ganho potencial de score
    - Sugere substituições ou novas contratações
    """
    try:
        sugestoes = []
        jogadores_pos = equipe_atual[equipe_atual['Posição'] == posicao_alvo]
        disponiveis = df[
            (~df['Nome'].isin(equipe_atual['Nome'])) &
            (df['Posição'] == posicao_alvo) &
            ~df['Lesionado'] &
            ~df['Expulso']
        ].sort_values('Score Ajustado', ascending=False)
        
        for _, candidato in disponiveis.iterrows():
            if len(sugestoes) >= 3:
                break
            
            if not jogadores_pos.empty:
                # Substituição com venda
                substituto = jogadores_pos.nsmallest(1, 'Score Ajustado').iloc[0]
                novo_orcamento = orcamento + substituto['Preço']
                
                if candidato['Preço'] <= novo_orcamento:
                    sugestoes.append({
                        'Tipo': 'Substituição',
                        'Sair': substituto['Nome'],
                        'Entrar': candidato['Nome'],
                        'Custo Líquido': candidato['Preço'] - substituto['Preço'],
                        'Ganho Score': candidato['Score Ajustado'] - substituto['Score Ajustado'],
                        'Detalhes Venda': substituto[['Nome', 'Preço', 'Score Ajustado']].to_dict(),
                        'Detalhes Compra': candidato[['Nome', 'Preço', 'Score Ajustado', 'Próximo Adversário', 'Dificuldade do Jogo']].to_dict()
                    })
            else:
                # Contratação direta
                if candidato['Preço'] <= orcamento:
                    sugestoes.append({
                        'Tipo': 'Contratação',
                        'Jogador': candidato['Nome'],
                        'Custo': candidato['Preço'],
                        'Ganho Score': candidato['Score Ajustado'],
                        'Detalhes': candidato[['Nome', 'Preço', 'Score Ajustado', 'Próximo Adversário', 'Dificuldade do Jogo']].to_dict()
                    })
        
        return sorted(sugestoes, key=lambda x: x['Ganho Score'], reverse=True)[:3]
    except Exception as e:
        print(f"ERRO NAS SUGESTÕES DE TRANSFERÊNCIA: {str(e)}")
        return []

def mostrar_equipe(titulares, substitutos):
    """
    Exibe a equipe titular e os substitutos sugeridos
    """
    print("\n=== Equipe Titular ===")
    for _, jogador in titulares.iterrows():
        print(f"{jogador['Posição']}: {jogador['Nome']} | Score: {jogador['Score Ajustado']:.2f}")
    
    print("\n=== Substitutos Sugeridos ===")
    for posicao, jogadores in substitutos.items():
        print(f"\n{posicao}:")
        for jogador in jogadores:
            print(f"  {jogador['Nome']} | Score: {jogador['Score Ajustado']:.2f}")

def interface_usuario():
    """
    Interface principal do programa
    - Gerencia o fluxo de interações com o usuário
    - Chama as funções apropriadas com base nas escolhas do usuário
    """
    try:
        df = carregar_dados("jogadores.xlsx")
        df = calcular_metricas(df)
        equipe_atual = obter_equipe_atual(df)
        
        while True:
            print("\n=== LIGA RECORD PRO ===")
            print("1. Melhor Equipa com Substitutos Sugeridos")
            print("2. Comparar Táticas")
            print("3. Sugerir Capitão")
            print("4. Sugerir Transferências")
            print("5. Sair")
            
            opcao = input("Escolha uma opção: ")
            
            if opcao == '1':
                tatica = input("Formação desejada (ex: 4-4-2): ").strip()
                titulares = selecionar_melhor_onze(equipe_atual, tatica)
                substitutos = sugerir_substitutos(equipe_atual)
                mostrar_equipe(titulares, substitutos)
            
            elif opcao == '2':
                melhores_taticas = comparar_taticas(equipe_atual)
                print("\nMelhores Táticas:")
                for i, (tatica, score, requisitos) in enumerate(melhores_taticas, 1):
                    print(f"{i}. {tatica} - Score: {score:.2f}")
                    print(f"   Requisitos: {requisitos}")
            
            elif opcao == '3':
                capitaes = sugerir_capitao(equipe_atual)
                print("\nMelhores opções para Capitão:")
                for _, capitao in capitaes.iterrows():
                    print(f"{capitao['Nome']} ({capitao['Posição']}) - Score: {capitao['Score Capitão']:.2f}")
                    print(f"Próximo jogo: {capitao['Próximo Adversário']} (Dificuldade: {capitao['Dificuldade do Jogo']})")
            
            elif opcao == '4':
                print("\nPosições disponíveis:")
                print("1. Goleiro\n2. Defesa\n3. Médio\n4. Avançado")
                escolha = input("Escolha a posição para transferência: ").strip()
                posicoes = {'1': 'Goleiro', '2': 'Defesa', '3': 'Médio', '4': 'Avançado'}
                
                if escolha in posicoes:
                    posicao = posicoes[escolha]
                    try:
                        orcamento = float(input("Orçamento disponível para transferências: €"))
                        sugestoes = sugerir_transferencias(df, equipe_atual, orcamento, posicao)
                        
                        if sugestoes:
                            print(f"\nTop 3 Sugestões para {posicao}:")
                            for i, sug in enumerate(sugestoes, 1):
                                print(f"\n{i}. {sug['Tipo']}:")
                                if sug['Tipo'] == 'Substituição':
                                    print(f"   Vender: {sug['Sair']} | Comprar: {sug['Entrar']}")
                                    print(f"   Custo Líquido: €{sug['Custo Líquido']:.2f}")
                                else:
                                    print(f"   Contratar: {sug['Jogador']}")
                                    print(f"   Custo: €{sug['Custo']:.2f}")
                                print(f"   Ganho de Score: +{sug['Ganho Score']:.2f}")
                                print(f"   Próximo Adversário: {sug['Detalhes Compra' if 'Detalhes Compra' in sug else 'Detalhes']['Próximo Adversário']}")
                                print(f"   Dificuldade: {sug['Detalhes Compra' if 'Detalhes Compra' in sug else 'Detalhes']['Dificuldade do Jogo']}")
                        else:
                            print("Nenhuma sugestão viável encontrada.")
                    except ValueError:
                        print("Valor de orçamento inválido!")
                else:
                    print("Opção de posição inválida!")
            
            elif opcao == '5':
                print("Obrigado por usar o LIGA RECORD PRO!")
                break
            
            else:
                print("Opção inválida. Por favor, tente novamente.")
    
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
    finally:
        print("Programa encerrado.")

if __name__ == "__main__":
    interface_usuario()
