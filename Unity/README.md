# Gêmeo Digital — Esteira de Pintura

Protótipo conceitual de um **gêmeo digital** de uma esteira de pintura industrial, desenvolvido como tutorial prático para um capítulo de livro sobre gêmeos digitais.

O projeto tem duas partes que conversam entre si:

1. **Ambiente virtual (Unity)** — simula a esteira, as caixas, os sensores e os cabeçotes de pintura.
2. **Dashboard web (Python/FastAPI)** — recebe os eventos do ambiente virtual em tempo real e mostra o que está acontecendo na linha de produção.

O dashboard foi feito para ser **universal**: nos próximos tutoriais, a mesma esteira será refeita em **Unreal Engine** e **NVIDIA Isaac Sim**, reutilizando exatamente este mesmo dashboard.

---

## O cenário

A esteira transporta caixas (gabinetes metálicos industriais) por três etapas de tratamento superficial:

| Ponto   | Sensor     | Cabeçote     | Aplicação              |
| ------- | ---------- | ------------ | ---------------------- |
| Entrada | `Sensor_1` | —            | Entrada do processo    |
| Ponto A | `Sensor_2` | `Cabecote_1` | Pintura de base        |
| Ponto B | `Sensor_3` | `Cabecote_2` | Tinta de acabamento    |
| Ponto C | `Sensor_4` | `Cabecote_3` | Verniz protetor        |

Depois do Ponto C, a caixa segue para a área de **expedição**.

---

## Estrutura do repositório

```
gemeo-digital-esteira/
├── EsteiraGD_Unity/        # Projeto Unity (ambiente virtual da esteira)
├── DashboardWeb_Python/    # Dashboard web em FastAPI
├── Modelos3D/              # Modelos 3D originais (.blend e .fbx)
├── .gitattributes          # Configuração do Git LFS e fim de linha
└── README.md
```

---

## Pré-requisitos

- **Git** com **Git LFS** instalado — os modelos 3D e texturas ficam no LFS.
- **Unity 6000.3.23f1** (ou compatível), com **URP** (Universal Render Pipeline).
- **Python 3.10+** para o dashboard.

### Clonando o repositório

Como o projeto usa Git LFS, instale-o **uma vez** na sua máquina antes de clonar:

```bash
git lfs install
git clone <url-do-repositorio>
```

Se você já havia clonado antes de instalar o LFS, baixe os binários com:

```bash
git lfs pull
```

---

## Como rodar o Dashboard

A forma mais simples (Windows):

1. Entre na pasta `DashboardWeb_Python`.
2. Dê **dois cliques** em `start_dashboard.bat`.
3. O navegador abre automaticamente em **http://localhost:8000**.

O `.bat` cria o ambiente virtual, instala as dependências e inicia o servidor. Se ele não funcionar, as instruções manuais estão comentadas no topo de `DashboardWeb_Python/main.py`.

### Cores do dashboard

- **Vermelho** — sensores
- **Amarelo** — cabeçotes (aplicadores)
- A caixa muda de cor conforme é pintada: **base → acabamento → verniz**.

---

## Como abrir o projeto Unity

1. Abra o **Unity Hub** e adicione a pasta `EsteiraGD_Unity`.
2. Abra o projeto com a versão **6000.3.17f1**.
3. Abra a cena `Assets/Scenes/SampleScene.unity` e clique em **Play**.

Com o dashboard rodando em paralelo, os eventos aparecem em tempo real na página. O objeto `ClienteDashboardWeb` da cena tem o campo **Nome da Fonte** (padrão `Unity`), que identifica a origem dos dados no dashboard.

> Se o servidor do dashboard estiver desligado, a simulação continua funcionando normalmente — apenas um aviso aparece no Console do Unity.

---

## Contrato de eventos (integração)

O ambiente virtual envia eventos para o dashboard via **HTTP POST** em `http://localhost:8000/api/eventos`, usando um JSON simples:

```json
{
  "tipo": "sensor",
  "origem": "Sensor_2",
  "caixa": "Caixa 1",
  "estagio": "Ponto A - pintura de base",
  "mensagem": "Caixa 1 detectada no Ponto A",
  "fonte": "Unity"
}
```

- `tipo`: `"sensor"` ou `"cabecote"`.
- `origem`: identificador do elemento (ex.: `Sensor_2`, `Cabecote_1`).
- `caixa`: nome da caixa (ex.: `Caixa 1`).
- `estagio`: descrição da etapa.
- `mensagem`: texto livre exibido no histórico.
- `fonte`: quem enviou (`Unity`, `Unreal`, `Isaac Sim`...).

Qualquer programa capaz de enviar esse JSON consegue alimentar o dashboard — é o que torna a integração reutilizável entre os tutoriais.

### Endpoints do dashboard

| Método | Rota            | Função                                          |
| ------ | --------------- | ----------------------------------------------- |
| `GET`  | `/`             | Abre a página do dashboard.                     |
| `POST` | `/api/eventos`  | Recebe um evento de qualquer fonte.             |
| `GET`  | `/eventos`      | Fluxo em tempo real (SSE) para o navegador.     |
| `GET`  | `/api/estado`   | Devolve o histórico em memória.                 |
| `POST` | `/api/limpar`   | Apaga o histórico (recomeçar um teste).         |
| `GET`  | `/api/health`   | Verifica se o servidor está no ar.              |

---

## Próximos tutoriais

A mesma esteira, com as mesmas funcionalidades, será reconstruída em:

- **Unreal Engine**
- **NVIDIA Isaac Sim**

Em ambos, basta enviar os eventos no formato acima (mudando o campo `fonte`) para reaproveitar este dashboard sem alterações.
