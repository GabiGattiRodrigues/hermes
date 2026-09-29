# 🗺️ Hermes: onde está o cliente da loja de bairro?

<img src="app/assets/hermes.png" width="360" alt="Hermes">

**Área de 15 minutos a pé, perfil de quem mora e trabalha perto e mix de produtos ideal** para cada
loja de uma rede fictícia de mercados de proximidade em São Paulo, construído com **dados públicos reais**.

> A rede **Ágora Express é fictícia**, com pontos em bairros reais. População, renda, empregos,
> gastos e ruas vêm de **dados públicos reais**. As **vendas das lojas são sintéticas** e servem só
> para demonstrar a análise de gap de sortimento.

## Pergunta de negócio
A rede usa a **mesma gôndola em todas as lojas**. Faz sentido? Quem vive e quem trabalha a 15 min a
pé de cada loja, e o que essas pessoas compram?

## Fontes de dados
| Fonte | O que usamos | Link |
|---|---|---|
| **Censo 2022 (IBGE)**, agregados por setor censitário | população, domicílios, idade e renda do responsável nos ~27 mil setores da capital | [FTP IBGE](https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/) |
| **Pesquisa Origem-Destino 2023 (Metrô-SP)** | coordenada do local de trabalho + fator de expansão → empregos perto da loja | [Portal da Transparência Metrô](https://transparencia.metrosp.com.br/dataset/pesquisa-origem-e-destino-2023-anexos) |
| **POF 2017-2018 (IBGE)**, SIDRA 6972 | gasto mensal das famílias de SP por tipo de alimento e classe de renda | [SIDRA 6972](https://sidra.ibge.gov.br/tabela/6972) |
| **IPCA (IBGE)**, SIDRA 1737 | deflator jan/2018 → jul/2022 | [SIDRA 1737](https://sidra.ibge.gov.br/tabela/1737) |
| **OpenStreetMap** (via `osmnx`) | rede de caminhada (isócronas) e supermercados/lojas de conveniência | [openstreetmap.org](https://www.openstreetmap.org/copyright) |

## Método (resumo)
1. **Isócrona de 15 min** pela rede de ruas do OSM (1.200 m de caminhada a 4,8 km/h).
2. **Quem mora:** setores do Censo cruzados com a isócrona (interpolação por área).
3. **Quem trabalha:** soma dos pesos da Pesquisa OD com local de trabalho dentro da área.
4. **Quanto gastam:** renda do responsável → renda familiar → classe POF (com IPCA). Domicílios ×
   gasto médio da classe por categoria, somado ao lanche/bebida dos trabalhadores.
5. **Índice de afinidade:** mix da área ÷ mix da cidade × 100.
6. **Perfis de loja:** k-means (k=4) sobre renda, idade, empregos por morador e densidade.
7. **Mix × vendas (sintético):** onde o potencial pesa mais que as vendas → *Ampliar*.

Premissas e limitações estão explícitas em `src/hermes/config.py`, no notebook e na aba
**Dados e método** do app.

## Como rodar (Windows)
1. `rodar_pipeline.bat` cria o ambiente, instala as bibliotecas, baixa os dados (~400 MB) e gera `dados/processados/`.
2. `rodar_app.bat` abre o app Streamlit.
3. `notebooks/hermes.ipynb` traz o passo a passo comentado.

## Estrutura
```
src/hermes/   config · fontes · censo · od · pof · osm · analise · vendas · pipeline
app/          app Streamlit (PT/EN)
notebooks/    notebook explicado
dados/processados/   saídas leves usadas pelo app (versionadas)
```

---
*English: 15-minute walking catchments for a fictional São Paulo grocery chain, built from real public
data (2022 Census, 2023 OD Survey, POF household budget survey, OpenStreetMap). The project turns them
into category-level spending potential, an affinity index vs. the city, store profiles (k-means) and a
product-mix recommendation against synthetic sales. The app is bilingual (PT/EN).*

Projeto de portfólio de **Gabriela Gatti Rodrigues** · [LinkedIn](https://www.linkedin.com/in/gabriela-gatti-rodrigues) · [Portfólio](https://gabigattirodrigues.github.io/)
