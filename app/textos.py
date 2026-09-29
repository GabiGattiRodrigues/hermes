"""Textos do app em português e inglês (tradução feita à mão, não automática)."""

T = {
    "titulo": {"pt": "Hermes · Onde está o cliente da loja de bairro?",
               "en": "Hermes · Where is the neighborhood store's customer?"},
    "subtitulo": {
        "pt": "Área de 15 minutos a pé, perfil de quem mora e trabalha perto e o mix de produtos ideal "
              "para cada loja de uma rede fictícia de mercados de proximidade em São Paulo.",
        "en": "15-minute walking catchment, profile of who lives and works nearby, and the ideal product "
              "mix for each store of a fictional convenience-grocery chain in São Paulo."},
    "aviso_ficticio": {
        "pt": "A rede **{rede}** é fictícia. Os dados de população, renda, empregos, gastos e ruas são "
              "**públicos e reais**; as **vendas** das lojas são **sintéticas** (simuladas).",
        "en": "The **{rede}** chain is fictional. Population, income, jobs, spending and street data are "
              "**real public data**; store **sales** are **synthetic** (simulated)."},
    "idioma": {"pt": "Idioma", "en": "Language"},
    "loja": {"pt": "Loja", "en": "Store"},
    "aba_mapa": {"pt": "🗺️ Mapa", "en": "🗺️ Map"},
    "aba_loja": {"pt": "🏪 Raio-X da loja", "en": "🏪 Store deep-dive"},
    "aba_comparar": {"pt": "📊 Comparar lojas", "en": "📊 Compare stores"},
    "aba_vendas": {"pt": "🛒 Mix × vendas", "en": "🛒 Mix × sales"},
    "aba_dados": {"pt": "📚 Dados e método", "en": "📚 Data & method"},
    # mapa
    "camadas": {"pt": "Camadas do mapa", "en": "Map layers"},
    "cam_renda": {"pt": "Renda média do responsável (setores)", "en": "Head-of-household mean income (tracts)"},
    "cam_trab": {"pt": "Onde as pessoas trabalham (OD 2023)", "en": "Where people work (OD 2023)"},
    "cam_conc": {"pt": "Concorrentes (OpenStreetMap)", "en": "Competitors (OpenStreetMap)"},
    "legenda_iso": {"pt": "Cor da área = perfil da loja", "en": "Area color = store profile"},
    "mapa_dica": {
        "pt": "Cada mancha é a área alcançável em **15 min a pé pelas ruas** (não é um círculo). "
              "Clique nas lojas e nos setores para ver detalhes.",
        "en": "Each shape is the area reachable in **15 min walking along streets** (not a circle). "
              "Click stores and tracts for details."},
    # KPIs
    "moradores": {"pt": "Moradores", "en": "Residents"},
    "domicilios": {"pt": "Domicílios", "en": "Households"},
    "empregos": {"pt": "Empregos", "en": "Jobs"},
    "renda": {"pt": "Renda média do resp.", "en": "Mean head-of-hh income"},
    "concorrentes": {"pt": "Concorrentes", "en": "Competitors"},
    "potencial": {"pt": "Potencial alimentar", "en": "Food spending potential"},
    "por_mes": {"pt": "/mês", "en": "/month"},
    "perfil": {"pt": "Perfil", "en": "Profile"},
    "idade_titulo": {"pt": "Idade de quem mora na área", "en": "Age of residents in the area"},
    "vs_cidade": {"pt": "Cidade de SP", "en": "São Paulo city"},
    "indice_titulo": {"pt": "Índice de afinidade por categoria (100 = média da cidade)",
                      "en": "Category affinity index (100 = city average)"},
    "indice_expl": {
        "pt": "Quanto o peso de cada categoria no gasto potencial da área difere da cidade. "
              "**120** = a vizinhança gasta proporcionalmente 20% a mais naquilo.",
        "en": "How much each category's share of the area's spending potential differs from the city. "
              "**120** = the neighborhood spends proportionally 20% more on it."},
    "quem_gasta": {"pt": "De onde vem o potencial: moradores × trabalhadores",
                   "en": "Where potential comes from: residents × workers"},
    "moradores_s": {"pt": "Moradores", "en": "Residents"},
    "trabalhadores_s": {"pt": "Trabalhadores", "en": "Workers"},
    "categoria": {"pt": "Categoria", "en": "Category"},
    "rs_mes": {"pt": "R$/mês", "en": "BRL/month"},
    "leitura": {"pt": "Como ler", "en": "How to read"},
    # comparar
    "comp_scatter": {"pt": "Renda × intensidade de empregos (tamanho = potencial)",
                     "en": "Income × job intensity (size = potential)"},
    "comp_eixo_x": {"pt": "Empregos por morador", "en": "Jobs per resident"},
    "comp_eixo_y": {"pt": "Renda média do responsável (R$)", "en": "Head-of-hh mean income (BRL)"},
    "comp_heat": {"pt": "Índice de afinidade: lojas × categorias", "en": "Affinity index: stores × categories"},
    "comp_tabela": {"pt": "Resumo das lojas", "en": "Store summary"},
    # vendas
    "vendas_aviso": {
        "pt": "⚠️ **Vendas sintéticas.** Simulamos que hoje a rede usa o **mesmo planograma** em todas as lojas. "
              "As vendas ficam entre o que a vizinhança quer e o que a gôndola padrão oferece. "
              "A diferença é a oportunidade de ajuste do mix.",
        "en": "⚠️ **Synthetic sales.** We simulate that the chain currently uses the **same planogram** in every "
              "store. Sales land between what the neighborhood wants and what the standard shelf offers. "
              "The difference is the mix-adjustment opportunity."},
    "vendas_mes": {"pt": "Vendas mensais (R$)", "en": "Monthly sales (BRL)"},
    "mix_titulo": {"pt": "Peso da categoria: potencial da área × vendas atuais",
                   "en": "Category share: area potential × current sales"},
    "potencial_s": {"pt": "Potencial da área", "en": "Area potential"},
    "vendas_s": {"pt": "Vendas atuais", "en": "Current sales"},
    "recomendacao": {"pt": "Recomendação de mix", "en": "Mix recommendation"},
    "acao": {"pt": "Ação", "en": "Action"},
    "oportunidade": {"pt": "Oportunidade (R$/mês)", "en": "Opportunity (BRL/month)"},
    "Ampliar": {"pt": "Ampliar", "en": "Expand"},
    "Reduzir": {"pt": "Reduzir", "en": "Reduce"},
    "Manter": {"pt": "Manter", "en": "Keep"},
    "mes": {"pt": "Mês", "en": "Month"},
    # dados
    "fontes_titulo": {"pt": "De onde vêm os dados", "en": "Where the data comes from"},
    "metodo_titulo": {"pt": "Como o cálculo é feito", "en": "How the calculation works"},
    "premissas_titulo": {"pt": "Premissas (hipóteses explícitas)", "en": "Assumptions (made explicit)"},
    "limites_titulo": {"pt": "Limitações – o que este projeto NÃO diz",
                       "en": "Limitations – what this project does NOT say"},
    "baixado": {"pt": "baixado em", "en": "downloaded on"},
    "sobre": {"pt": "Projeto de portfólio de **Gabriela Gatti Rodrigues**, cientista de dados. "
                    "[LinkedIn](https://www.linkedin.com/in/gabriela-gatti-rodrigues) · "
                    "[Portfólio](https://gabigattirodrigues.github.io/)",
              "en": "Portfolio project by **Gabriela Gatti Rodrigues**, data scientist. "
                    "[LinkedIn](https://www.linkedin.com/in/gabriela-gatti-rodrigues) · "
                    "[Portfolio](https://gabigattirodrigues.github.io/)"},
}

FONTES = [
    {
        "nome": {"pt": "Censo Demográfico 2022 – Agregados por setores censitários (IBGE)",
                 "en": "2022 Demographic Census – Aggregates by census tract (IBGE)"},
        "chave": ["Censo 2022 – malha de setores (SP)", "Censo 2022 – agregados de demografia",
                  "Censo 2022 – rendimento do responsável"],
        "o_que": {"pt": "Malha dos ~27 mil setores da capital com população e domicílios; população por "
                        "faixa etária; rendimento nominal médio do responsável pelo domicílio.",
                  "en": "Boundaries of the city's ~27k census tracts with population and households; "
                        "population by age group; mean nominal income of the head of household."},
        "uso": {"pt": "Quem MORA dentro da área de 15 min de cada loja (idade, renda, nº de domicílios).",
                "en": "Who LIVES within each store's 15-min area (age, income, number of households)."},
        "link": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/",
    },
    {
        "nome": {"pt": "Pesquisa Origem-Destino 2023 (Metrô-SP)",
                 "en": "2023 Origin-Destination Survey (São Paulo Metro)"},
        "chave": ["Pesquisa Origem-Destino 2023 (Metrô-SP)"],
        "o_que": {"pt": "Microdados de ~30 mil domicílios entrevistados na Região Metropolitana, com a "
                        "coordenada do local de trabalho de cada pessoa e o fator de expansão (quantas pessoas "
                        "reais cada entrevistado representa).",
                  "en": "Microdata from ~30k surveyed households in the metro region, with each person's "
                        "workplace coordinates and an expansion weight (how many real people each "
                        "respondent represents)."},
        "uso": {"pt": "Quem TRABALHA perto da loja: soma dos pesos dos locais de trabalho dentro da área.",
                "en": "Who WORKS near the store: sum of workplace weights inside the area."},
        "link": "https://transparencia.metrosp.com.br/dataset/pesquisa-origem-e-destino-2023-anexos",
    },
    {
        "nome": {"pt": "Pesquisa de Orçamentos Familiares 2017-2018 (IBGE, SIDRA tabela 6972)",
                 "en": "Household Budget Survey 2017-2018 (IBGE, SIDRA table 6972)"},
        "chave": ["POF 2017-2018 – despesa com alimentação (SIDRA 6972, SP)"],
        "o_que": {"pt": "Gasto médio mensal das famílias do estado de SP com cada tipo de alimento "
                        "(arroz, carnes, leite, pão, bebidas…), por classe de renda familiar.",
                  "en": "Average monthly spending of São Paulo state families on each food type "
                        "(rice, meat, milk, bread, drinks…), by family income bracket."},
        "uso": {"pt": "Converte o perfil de renda da área em R$ por categoria de gôndola.",
                "en": "Turns the area's income profile into BRL per shelf category."},
        "link": "https://sidra.ibge.gov.br/tabela/6972",
    },
    {
        "nome": {"pt": "IPCA – número-índice (IBGE, SIDRA tabela 1737)",
                 "en": "IPCA consumer price index (IBGE, SIDRA table 1737)"},
        "chave": ["IPCA – número-índice (SIDRA 1737)"],
        "o_que": {"pt": "Inflação oficial entre jan/2018 (data da POF) e jul/2022 (data do Censo).",
                  "en": "Official inflation between Jan/2018 (POF date) and Jul/2022 (Census date)."},
        "uso": {"pt": "Coloca renda do Censo e gasto da POF na mesma moeda.",
                "en": "Puts Census income and POF spending in the same currency."},
        "link": "https://sidra.ibge.gov.br/tabela/1737",
    },
    {
        "nome": {"pt": "OpenStreetMap (via osmnx)", "en": "OpenStreetMap (via osmnx)"},
        "chave": [],
        "o_que": {"pt": "Rede de ruas e calçadas para caminhada e pontos de supermercados/lojas de "
                        "conveniência (tags shop=supermarket e shop=convenience).",
                  "en": "Walkable street network and supermarket/convenience store points "
                        "(tags shop=supermarket and shop=convenience)."},
        "uso": {"pt": "Desenha a área REAL de 15 min a pé e conta os concorrentes dentro dela.",
                "en": "Draws the REAL 15-min walking area and counts competitors inside it."},
        "link": "https://www.openstreetmap.org/copyright",
    },
    {
        "nome": {"pt": "Valhalla – motor de rotas open source (servidor público FOSSGIS)",
                 "en": "Valhalla – open-source routing engine (FOSSGIS public server)"},
        "chave": [],
        "o_que": {"pt": "Calcula rotas e isócronas a pé sobre a mesma malha de ruas do OpenStreetMap.",
                  "en": "Computes walking routes and isochrones on the same OpenStreetMap street network."},
        "uso": {"pt": "Entrega o polígono de 15 min pronto, em ~1 s por loja. O cálculo passo a passo com "
                      "osmnx (mostrado no notebook) é o plano B.",
                "en": "Returns the ready-made 15-min polygon in ~1 s per store. The step-by-step osmnx "
                      "calculation (shown in the notebook) is the fallback."},
        "link": "https://valhalla.github.io/valhalla/",
    },
]

METODO = {
    "pt": """
1. **Área de 15 min (isócrona).** Para cada loja, baixamos a rede de caminhada do OpenStreetMap e calculamos
   todos os trechos alcançáveis andando {dist:,.0f} m (15 min a {vel} km/h). Esses trechos viram um polígono.
2. **Quem mora.** Cruzamos o polígono com os setores censitários. Se 40% de um setor cai na área,
   contamos 40% das pessoas e domicílios dele (*interpolação por área*).
3. **Quem trabalha.** Somamos o fator de expansão dos entrevistados da Pesquisa OD cujo local de trabalho
   cai dentro da área.
4. **Quanto gastam.** A renda do responsável (Censo, jul/2022) vira renda familiar (× {fam}) e é
   deflacionada pelo IPCA (÷ {ipca:.2f}) para cair numa classe de renda da POF. Cada domicílio "herda" o gasto
   médio da sua classe em cada categoria. Os trabalhadores somam o gasto com lanche e bebida fora de casa.
5. **Índice de afinidade.** Comparamos o mix de gasto da área com o mix da cidade inteira (100 = igual).
6. **Perfis de loja.** k-means (k=4) sobre renda, % de crianças, % de idosos, empregos por morador e
   densidade. Os grupos recebem nome pelo que mais se destaca no centro de cada um.
7. **Mix × vendas (sintético).** Comparamos o peso de cada categoria no potencial com o peso nas vendas
   simuladas. Diferença relativa ≥ 5% → *Ampliar*; ≤ −5% → *Reduzir*.
""",
    "en": """
1. **15-min area (isochrone).** For each store we download the OpenStreetMap walking network and find every
   segment reachable within {dist:,.0f} m (15 min at {vel} km/h). Those segments become a polygon.
2. **Who lives there.** We intersect the polygon with census tracts. If 40% of a tract falls inside the area,
   we count 40% of its people and households (*areal interpolation*).
3. **Who works there.** We add up the expansion weights of OD Survey respondents whose workplace falls
   inside the area.
4. **How much they spend.** Head-of-household income (Census, Jul/2022) becomes family income (× {fam}) and
   is deflated by IPCA (÷ {ipca:.2f}) to land in a POF income bracket. Each household "inherits" its bracket's
   average spending per category. Workers add their out-of-home snack and drink spending.
5. **Affinity index.** We compare the area's spending mix with the whole city's mix (100 = equal).
6. **Store profiles.** k-means (k=4) on income, % children, % elderly, jobs per resident and density. Groups
   are named after what stands out most in each centroid.
7. **Mix × sales (synthetic).** We compare each category's share of potential with its share of simulated
   sales. Relative gap ≥ 5% → *Expand*; ≤ −5% → *Reduce*.
""",
}

PREMISSAS_TXT = {
    "minutos_caminhada": {"pt": "Minutos de caminhada", "en": "Walking minutes"},
    "velocidade_km_h": {"pt": "Velocidade a pé (km/h)", "en": "Walking speed (km/h)"},
    "fator_renda_familia": {"pt": "Renda da família ÷ renda do responsável",
                            "en": "Family income ÷ head-of-household income"},
    "trabalhadores_por_familia": {"pt": "Trabalhadores por família", "en": "Workers per family"},
    "parcela_trabalhador_mercado": {"pt": "Parcela do lanche do trabalhador que o mercado disputa",
                                    "en": "Share of worker snack spending a grocery can compete for"},
}

LIMITES = {
    "pt": """
- **Potencial ≠ venda.** É quanto a vizinhança gasta com alimentos para casa, em qualquer lugar, não
  quanto a loja vai vender.
- **POF de 2017-18 e por estado.** Hábitos mudaram desde então e o recorte é o estado de SP, não o bairro.
  Duas áreas com a mesma renda recebem o mesmo "carrinho".
- **Renda do responsável ≠ renda da família.** A conversão usa uma premissa fixa (acima).
- **Setores com renda sob sigilo** recebem a distribuição de renda dos vizinhos da mesma área.
- **Pesquisa OD é amostral.** Em áreas pequenas, o número de empregos tem margem de erro relevante.
- **OpenStreetMap é colaborativo.** A lista de concorrentes pode estar incompleta.
- **Vendas são sintéticas**, feitas para demonstrar a análise de gap. Com dados reais da empresa, o mesmo
  código serviria para validar o potencial.
""",
    "en": """
- **Potential ≠ sales.** It is how much the neighborhood spends on groceries anywhere, not what the store will sell.
- **POF is from 2017-18 and state-level.** Habits have changed, and the breakdown is São Paulo state, not the
  neighborhood. Two areas with the same income get the same "basket".
- **Head-of-household income ≠ family income.** The conversion uses a fixed assumption (above).
- **Tracts with confidential income** get the income distribution of their neighbors in the same area.
- **The OD Survey is sample-based.** In small areas, job counts carry meaningful error.
- **OpenStreetMap is crowdsourced.** The competitor list may be incomplete.
- **Sales are synthetic**, built to demonstrate the gap analysis. With real company data, the same code
  would validate the potential.
""",
}

# ---------------------------------------------------------------------------
# Aba "O case" e explicações de conceitos
# ---------------------------------------------------------------------------
T.update({
    "aba_case": {"pt": "📖 O case", "en": "📖 The case"},
    "perfil_sidebar": {"pt": "Perfil da loja (k-means)", "en": "Store profile (k-means)"},
    "afinidade_titulo": {"pt": "📐 O que é o índice de afinidade?", "en": "📐 What is the affinity index?"},
    "kmeans_titulo": {"pt": "🧠 Como os perfis de loja foram criados: k-means",
                      "en": "🧠 How store profiles were built: k-means"},
    "kmeans_retrato": {"pt": "Retrato de cada perfil (desvio em relação à média das 15 lojas)",
                       "en": "Portrait of each profile (deviation from the 15-store average)"},
    "kmeans_centros": {"pt": "Centro de cada grupo, em valores reais", "en": "Each group's centroid, in real units"},
    "kmeans_k": {"pt": "Escolha do número de grupos (k)", "en": "Choosing the number of groups (k)"},
    "exemplo_loja": {"pt": "Exemplo nesta loja", "en": "Example for this store"},
})

CASE = {
    "pt": """
### O problema
Uma rede de mercados de proximidade (a **{rede}**, fictícia) tem 15 lojas espalhadas por São Paulo e usa
**a mesma gôndola em todas**. Só que uma loja na Faria Lima e outra no Capão Redondo atendem públicos
completamente diferentes: quem mora perto, quem trabalha perto, quanto ganham e o que colocam no carrinho.

### A pergunta de negócio
> **Para cada loja: quem está a 15 minutos a pé e o que essas pessoas compram? Onde o mix atual está
> desalinhado com a vizinhança?**

### Como o Hermes responde
1. **Área de influência real.** A área alcançável em 15 min a pé *pelas ruas* (isócrona), não um círculo.
2. **Quem mora e quem trabalha ali.** Censo 2022 (moradores, idade, renda) + Pesquisa OD 2023 (empregos).
3. **Quanto dinheiro circula por categoria.** O perfil de renda vira gasto por categoria de gôndola com a POF (IBGE).
4. **Índice de afinidade.** O que a vizinhança compra *mais* ou *menos* que a média da cidade.
5. **Perfis de loja (k-means).** As 15 lojas agrupadas em 4 "tipos", para ter 4 planogramas em vez de 15.
6. **Mix × vendas.** Onde a loja vende menos do que o potencial da área indica: ampliar ou reduzir espaço.

### Principais achados
{achados}

### Como navegar
- **🗺️ Mapa**: as áreas de 15 min, a renda por setor, onde se trabalha e os concorrentes.
- **🏪 Raio-X da loja**: perfil da vizinhança e o índice de afinidade da loja escolhida na barra lateral.
- **📊 Comparar lojas**: os **perfis criados com k-means** e o índice de todas as lojas lado a lado.
- **🛒 Mix × vendas**: recomendação de ampliar/reduzir cada categoria (vendas sintéticas).
- **📚 Dados e método**: de onde vem cada dado, premissas e limitações.
""",
    "en": """
### The problem
A convenience-grocery chain (the fictional **{rede}**) has 15 stores across São Paulo and uses **the same
shelf layout in all of them**. But a store in the Faria Lima business district and one in Capão Redondo
serve completely different people: who lives nearby, who works nearby, how much they earn and what goes
into their basket.

### The business question
> **For each store: who is within a 15-minute walk and what do they buy? Where is the current mix out of
> line with the neighborhood?**

### How Hermes answers it
1. **Real catchment area.** The area reachable in 15 min walking *along streets* (isochrone), not a circle.
2. **Who lives and who works there.** 2022 Census (residents, age, income) + 2023 OD Survey (jobs).
3. **How much money flows per category.** The income profile becomes spending per shelf category via the POF (IBGE).
4. **Affinity index.** What the neighborhood buys *more* or *less* than the city average.
5. **Store profiles (k-means).** The 15 stores grouped into 4 "types", so the chain needs 4 planograms instead of 15.
6. **Mix × sales.** Where the store sells less than the area's potential suggests: expand or shrink shelf space.

### Key findings
{achados}

### How to navigate
- **🗺️ Map**: 15-min areas, income by tract, where people work and competitors.
- **🏪 Store deep-dive**: the neighborhood profile and affinity index for the store picked in the sidebar.
- **📊 Compare stores**: the **k-means profiles** and every store's index side by side.
- **🛒 Mix × sales**: expand/shrink recommendation per category (synthetic sales).
- **📚 Data & method**: where each data point comes from, assumptions and limitations.
""",
}

AFINIDADE = {
    "pt": """
O índice compara **o peso de cada categoria no gasto potencial da vizinhança** com **o peso dessa mesma
categoria na cidade inteira**:

$$\\text{índice} = \\frac{\\%\\ \\text{da categoria no potencial da área}}{\\%\\ \\text{da categoria no potencial da cidade}} \\times 100$$

- **100** = a vizinhança gasta com aquilo na mesma proporção que a média de São Paulo.
- **acima de 100** = gasta proporcionalmente **mais** → candidata a ganhar espaço na gôndola.
- **abaixo de 100** = gasta proporcionalmente **menos** → candidata a perder espaço.

Por ser uma **proporção**, o índice não depende do tamanho da área: uma loja pequena e uma grande podem ser
comparadas diretamente. É a métrica que "conversa" com o time comercial.
""",
    "en": """
The index compares **each category's share of the neighborhood's spending potential** with **that same
category's share across the whole city**:

$$\\text{index} = \\frac{\\%\\ \\text{of the category in the area's potential}}{\\%\\ \\text{of the category in the city's potential}} \\times 100$$

- **100** = the neighborhood spends on it in the same proportion as the São Paulo average.
- **above 100** = proportionally **more** → a candidate for more shelf space.
- **below 100** = proportionally **less** → a candidate for less space.

Because it is a **proportion**, the index does not depend on the area's size: small and large stores can be
compared directly. It is the metric that speaks the commercial team's language.
""",
}

AFINIDADE_EXEMPLO = {
    "pt": "Em **{loja}**, **{cat}** representa **{s_loja:.1%}** do gasto potencial da área, contra **{s_cid:.1%}** na cidade → índice = {s_loja:.1%} ÷ {s_cid:.1%} × 100 = **{ind:.0f}**.",
    "en": "In **{loja}**, **{cat}** is **{s_loja:.1%}** of the area's spending potential, versus **{s_cid:.1%}** in the city → index = {s_loja:.1%} ÷ {s_cid:.1%} × 100 = **{ind:.0f}**.",
}

KMEANS = {
    "pt": """
**Por que agrupar?** Ter um planograma por loja é caro de operar. A ideia é achar poucos "tipos" de loja que
se parecem entre si e desenhar uma gôndola para cada tipo.

**O algoritmo: k-means.** Ele coloca as lojas em *k* grupos de forma que cada loja fique o mais perto
possível do "centro" do seu grupo. Na prática: sorteia *k* centros, liga cada loja ao centro mais próximo,
recalcula os centros como a média do grupo e repete até estabilizar (usamos 20 inícios diferentes e ficamos
com o melhor).

**As 5 variáveis usadas** (todas da área de 15 min de cada loja):
| Variável | O que captura |
|---|---|
| Renda média do responsável | poder de compra |
| % de crianças (0-14 anos) | famílias com filhos |
| % de idosos (60+) | bairros mais maduros |
| Empregos por morador *(em log)* | área de escritório × área residencial |
| Densidade (hab/km²) *(em log)* | verticalização / volume de gente |

**Padronização.** Antes do k-means cada variável vira *z-score* (média 0, desvio 1). Sem isso a renda, que
está na casa dos milhares, dominaria as porcentagens. Empregos e densidade entram em log porque variam em
ordens de grandeza.

**Nomes dos grupos.** O k-means só devolve números (0, 1, 2, 3). O nome vem do centro de cada grupo: o de
mais empregos por morador é *Corporativo*; entre os demais, o de mais crianças é *Periferia familiar*; e
assim por diante.
""",
    "en": """
**Why group?** Running one planogram per store is expensive. The idea is to find a few store "types" that
look alike and design one shelf layout per type.

**The algorithm: k-means.** It puts the stores into *k* groups so that each store is as close as possible to
its group's "center". In practice it picks *k* centers, assigns each store to the nearest one, recomputes
each center as the group average and repeats until it stabilizes (we use 20 random starts and keep the best).

**The 5 variables used** (all from each store's 15-min area):
| Variable | What it captures |
|---|---|
| Head-of-household mean income | purchasing power |
| % children (0-14) | families with kids |
| % elderly (60+) | more mature neighborhoods |
| Jobs per resident *(log)* | office district × residential area |
| Density (people/km²) *(log)* | high-rise / sheer volume of people |

**Standardization.** Before k-means each variable becomes a *z-score* (mean 0, sd 1). Otherwise income, in the
thousands, would drown out the percentages. Jobs and density enter in log because they span orders of magnitude.

**Group names.** k-means only returns numbers (0, 1, 2, 3). Names come from each group's center: the one with
the most jobs per resident is *Business district*; among the rest, the one with the most children is
*Family outskirts*; and so on.
""",
}

KMEANS_K = {
    "pt": "Testamos k de 2 a 6. A **silhueta** mede quão bem separados estão os grupos (de −1 a 1, maior é melhor). k=2 tem a maior silhueta, mas só separa \"periferia × resto\", o que é pouco útil para o negócio. **k=4 empata com k=5** e gera grupos com pelo menos 2 lojas, então é o equilíbrio entre separação estatística e número de planogramas que a operação consegue manter.",
    "en": "We tested k from 2 to 6. The **silhouette** measures how well separated the groups are (−1 to 1, higher is better). k=2 scores highest but only splits \"outskirts × everyone else\", which is of little business use. **k=4 ties with k=5** and yields groups of at least 2 stores, so it balances statistical separation with the number of planograms operations can maintain.",
}

# ---------------------------------------------------------------------------
# Aba "O case" – versão didática (conceitos com exemplos práticos)
# ---------------------------------------------------------------------------
CASE_RESUMO = {
    "pt": "**Em uma frase:** o Hermes descobre **quem vive e quem trabalha a 15 minutos a pé** de cada loja "
          "e traduz isso em **o que colocar na gôndola**. Tudo com dados públicos (IBGE, Metrô-SP e OpenStreetMap).",
    "en": "**In one sentence:** Hermes finds out **who lives and who works within a 15-minute walk** of each store "
          "and turns that into **what to put on the shelf**. All with public data (IBGE, São Paulo Metro and OpenStreetMap).",
}
CASE_PROBLEMA = {
    "pt": """
### 🎯 O problema
A **{rede}** (rede fictícia) tem 15 mercadinhos de bairro em São Paulo e usa **a mesma gôndola em todas as lojas**.
Mas pense em duas delas:

- a loja da **Faria Lima** fica no meio de prédios de escritório: de dia passam por ali mais de **{emp_fl} pessoas que trabalham** na região;
- a loja do **Capão Redondo** fica num bairro residencial, com muitas famílias com crianças e renda bem menor.

Faz sentido vender as mesmas coisas, nas mesmas quantidades, nas duas? **Não.** O Hermes mostra *quanto* e *onde* elas são diferentes.

> **Pergunta de negócio:** para cada loja, quem está a 15 min a pé, o que essas pessoas compram
> e onde o mix atual está desalinhado com a vizinhança?
""",
    "en": """
### 🎯 The problem
The fictional **{rede}** chain has 15 neighborhood grocery stores in São Paulo and uses **the same shelf layout in every store**.
But think about two of them:

- the **Faria Lima** store sits among office towers: over **{emp_fl} people work** in its area during the day;
- the **Capão Redondo** store is in a residential neighborhood, with many families with children and much lower income.

Does it make sense to sell the same things, in the same amounts, in both? **No.** Hermes shows *how much* and *where* they differ.

> **Business question:** for each store, who is within a 15-min walk, what do they buy
> and where is the current mix out of line with the neighborhood?
""",
}
CASE_CONCEITOS_TIT = {"pt": "🧩 Os conceitos, em linguagem simples", "en": "🧩 The concepts, in plain language"}
CASE_LOJAS_TIT = {"pt": "🔍 Na prática: duas lojas lado a lado", "en": "🔍 In practice: two stores side by side"}
CASE_ACHADOS_TIT = {"pt": "💡 Principais achados", "en": "💡 Key findings"}
CASE_NAVEGAR = {
    "pt": """
### 🧭 Como navegar
| Aba | O que você encontra |
|---|---|
| 🗺️ **Mapa** | as áreas de 15 min, a renda de cada quarteirão, onde se trabalha e os concorrentes |
| 🏪 **Raio-X da loja** | tudo sobre a loja escolhida na barra lateral, com o índice de afinidade explicado |
| 📊 **Comparar lojas** | como o **k-means** criou os 4 perfis, e todas as lojas lado a lado |
| 🛒 **Mix × vendas** | o que ampliar ou reduzir em cada loja (vendas simuladas) |
| 📚 **Dados e método** | de onde vem cada dado, premissas e limitações |
""",
    "en": """
### 🧭 How to navigate
| Tab | What you'll find |
|---|---|
| 🗺️ **Map** | 15-min areas, income per block, where people work and competitors |
| 🏪 **Store deep-dive** | everything about the store picked in the sidebar, with the affinity index explained |
| 📊 **Compare stores** | how **k-means** built the 4 profiles, and all stores side by side |
| 🛒 **Mix × sales** | what to expand or shrink in each store (simulated sales) |
| 📚 **Data & method** | where each data point comes from, assumptions and limitations |
""",
}
