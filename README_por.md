<!-- =============================================================================
HYDRA-UMC-DEVELOPER-NODE - Developer node: evidence, repro cases and checkouts, approved by a person
Copyright (C) JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
GPL-3.0-or-later - see LICENSE
============================================================================= -->

<p align="center">
  <img src="images/HYDRA_UMC_BANNER.svg" alt="HYDRA-UMC-DEVELOPER-NODE banner" width="100%">
</p>

# 🧑‍💻 HYDRA-UMC-DEVELOPER-NODE

<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README_spa.md">🇪🇸 Español</a> | <a href="README_fra.md">🇫🇷 Français</a> | <a href="README_ita.md">🇮🇹 Italiano</a> | <a href="README_deu.md">🇩🇪 Deutsch</a> | <a href="README_zho.md">🇨🇳 简体中文</a> | <a href="README_jpn.md">🇯🇵 日本語</a> | 🇵🇹 <b>Português</b></p>

### 🧑‍💻 Nó de desenvolvimento: estuda falhas, reproduz-as e não executa nada sem aprovação

<p align="center">
  <img src="https://img.shields.io/badge/License-GPL%203.0--or--later-blue.svg" alt="GPL 3.0 or later">
  <img src="https://img.shields.io/badge/Language-Python%203.11%2B-blue.svg" alt="Language">
  <img src="https://img.shields.io/badge/Core-stdlib%20only-brightgreen.svg" alt="Core">
  <img src="https://img.shields.io/badge/Parts-closed%20by%20default-367BF5.svg" alt="Parts">
  <img src="https://img.shields.io/badge/Tests-86%20passing-2ea44f.svg" alt="Tests">
  <img src="https://img.shields.io/badge/Version-0.0.2-0f6cbd.svg" alt="Version">
  <img src="https://img.shields.io/badge/Maturity-scaffolding-FFB020.svg" alt="Maturity">
</p>

---

**Verificação de honestidade - o que funciona hoje:** a ingestão de provas (assinatura, nonce, soma de verificação, verificação de segredos), os casos de reprodução executáveis com aprovações ligadas a um resumo, a cache de checkouts com o seu limite, o documento de estado, o plugin `ecosystem-ci` e os textos em oito idiomas são reais e estão testados (86 testes automáticos, com repositórios git locais e processos locais). O nó não correu num anfitrião de desenvolvimento real, uma receita não está isolada além de uma lista de permitidos e de um ambiente mínimo, e nada tira trabalho da fila sozinho. Veja o `CHANGELOG.md` para saber exatamente o que foi entregue.

---

> **Estado de segurança (safety e security):** este ecossistema não é um sistema de segurança certificado. Ainda não existe um caminho de E-STOP por hardware, nem limites ou interlocks impostos pelo firmware, nem um comando de movimento verificado; as imagens de firmware são verificadas com CRC-32 e uma assinatura Ed25519, e uma compilação de versão recusa as chaves de desenvolvimento publicadas (as cabeças de ferramenta e as placas de expansão atrás do relé ainda usam os bootloaders do URTC, que aceitam um HMAC-SHA256 de chave partilhada em vez de uma assinatura); TLS e TLS mútuo são opcionais e estão desativados por defeito; nenhuma placa própria foi ainda montada ou testada. Leia a [base de segurança](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/SECURITY_BASELINE.md) e o [modelo de ameaças](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/THREAT_MODEL.md) antes de confiar em qualquer afirmação aqui para a segurança de uma pessoa.

---

## 📋 Num relance

| | |
|---|---|
| Versão | `0.0.2` |
| Maturidade | Estrutura inicial |
| Testes | 86 (`python -m pytest -q tests`) |
| Tecnologia | Python 3.11+ / JSON Schema / SQLite / git worktree |
| Destino | Um servidor de desenvolvimento |
| Em hardware real | Não aplicável: nada aqui corre em hardware |

**Ir para:** [Visão geral](#-visão-geral) · [Arquitetura](#-arquitetura) · [Início rápido](#-início-rápido) · [Testes](#-testes) · [Estrutura do repositório](#-estrutura-do-repositório) · [Projetos relacionados](#-projetos-relacionados)

## 🚦 Estado do projeto

Cada linha é uma parte deste repositório e a luz diz até onde chega hoje. É escrita com o que o repositório consegue demonstrar (testes, compilações, execuções), não com o que está previsto.

🟢 Feito e verificado · 🟡 Funciona, com limites conhecidos · 🟠 Feito a meio ou ainda por verificar · 🔴 Por fazer ou a não funcionar

| Área | Estado | O que significa aqui |
|---|---|---|
| Software | 🟠 | Só estrutura e as primeiras peças; falta a maior parte do trabalho |
| Testes | 🟡 | 86 testes automáticos, executados a cada alteração |
| Hardware real | 🟡 | Não aplicável: nada aqui corre em hardware |
| Interface e protocolos | 🟡 | As rotas ou mensagens que oferece estão documentadas e testadas com um cliente; ainda nem todos os clientes as usaram |
| Integração | 🟡 | As suas mensagens e rotas são verificadas contra os contratos partilhados do SDK; ainda não funcionou em conjunto com o equipamento real |
| Segurança | 🟡 | O controlo de acesso, os limites de entrada ou as assinaturas estão implementados e testados num computador; ninguém fora do projeto os reviu |
| Operação | 🟠 | Escreve registos; ainda não tem ponto de métricas nem de saúde |
| Documentação | 🟡 | README em oito idiomas, verificado contra o manifesto a cada alteração |

## 🎯 Visão geral

O HYDRA-UMC-DEVELOPER-NODE é o nó de desenvolvimento do ecossistema: o lugar onde se estuda uma falha comunicada por um nó. Lê o pacote de provas do `HYDRA-UMC-LOCAL-TECHNICIAN` (só de leitura), obtém o código exato da revisão envolvida a partir de uma cache de worktrees do git, reproduz a falha com uma receita fixa e pode executar a CI partilhada sobre uma área de trabalho.

Quatro regras valem em todo o lado. Cada parte está **fechada** até o ficheiro de configuração a abrir. Nada é executado sem que **uma pessoa aprove exatamente o que vai ser executado**. Nada **sai da máquina**. Todo o valor ajustável vive no **ficheiro de configuração**, nunca no código.

Esta versão inclui cinco peças independentes:

1. **Ingestão de provas** (`evidence.py`) - verifica um pacote ou uma mensagem assinada `incident-transport/1` (assinatura, destinatário, idade, nonce, forma, soma de verificação, sem segredos) e guarda-o como um caso à espera de uma pessoa.
2. **Casos de reprodução executáveis** (`repro.py`, `approvals.py`) - uma receita de listas de argumentos, só comandos permitidos e uma aprovação ligada ao seu resumo; cada execução é um `ScenarioOutcome` do SDK e o SDK dá o veredito de um par antes e depois.
3. **Cache de checkouts por revisão** (`checkouts.py`) - um espelho bare e um worktree do git por commit, o commit fixado é verificado, um limite em GB é mantido removendo os worktrees menos usados recentemente.
4. **Documento de estado** (`panel.py`) - fila, diário e estado de saúde para um painel ou um estúdio, em oito idiomas, como um ficheiro.
5. **Plugin `ecosystem-ci`** (`plugin_ci.py`) - o validador de CI partilhado de cada repositório de uma área de trabalho, com um relatório consolidado. No modo completo (fechado por predefinição) também pode executar o teste pesado que cada repositório declara, como um lote que uma pessoa aprova pelo seu resumo, um repositório de cada vez, com limites de tempo, de saída e de espaço livre em disco.

## 🧩 Papel no HYDRA-UMC

O **HYDRA-UMC-DEVELOPER-NODE** é o nó de desenvolvimento do ecossistema: lê os pacotes de provas do `HYDRA-UMC-LOCAL-TECHNICIAN`, mantém uma cache de checkouts por revisão, executa receitas de reprodução e a CI partilhada, e cada uma destas partes fica fechada até a configuração a abrir e uma pessoa aprovar a execução exata.

## 🏛️ Arquitetura

<p align="center">
  <img src="images/architecture.svg" alt="HYDRA-UMC-DEVELOPER-NODE architecture" width="100%">
</p>

## 🚀 Início rápido

Requer Python 3.11 ou superior.

```bash
./build.sh  # Linux, macOS (build.bat on Windows)
./run.sh
./run.sh --config configs/developer-node.json evidence verify bundle.json
```

## 🧪 Testes

86 testes automáticos correm com `python -m pytest -q tests`. Não precisam de hardware nem de nada fora desta máquina.

A CI executa `HYDRA_UMC_CI=1 python tools/ci_validate.py`, que verifica o manifesto, os documentos, os oito README e as imagens.

## 🏗️ Compilação e publicação

```bash
chmod +x build.sh   # uma só vez
./build.sh          # cria .venv, pip install -e ".[dev]", verifica a compilação e corre os testes
./run.sh            # verifica a configuração incluída (todos os interruptores fechados)
./run.sh --config configs/developer-node.json evidence verify bundle.json
./run.sh --version
```

No Windows: `build.bat` e depois `run.bat`. `test.sh` / `test.bat` correm os testes e as verificações sem mudar a versão. O veredito de um par antes e depois precisa do SDK: `pip install -e ".[dev,sdk]"`.

**Resolução de problemas**

- `Recusado: ... is closed`: a parte está desativada. Abra-a no ficheiro de configuração (`"enabled": true`, um booleano verdadeiro) e leia [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
- `no valid approval for this exact recipe`: aprove a receita outra vez com `repro approve`; uma aprovação expira e serve uma só vez.
- `an approval needs a person at a terminal`: faça a aprovação num terminal, não a partir de um script ou de um pipe.

## 📂 Estrutura do repositório

<p align="center">
  <img src="images/repository-structure.svg" alt="Repository structure of HYDRA-UMC-DEVELOPER-NODE" width="100%">
</p>

<details>
<summary>Versão em texto da árvore</summary>

```text
HYDRA-UMC-DEVELOPER-NODE/
├── src/hydra_umc_developer_node/   código-fonte
│   ├── cli.py                      linha de comandos
│   ├── settings.py                 configuração e interruptores
│   ├── evidence.py                 verificação e ingestão de provas
│   ├── repro.py                    receitas de reprodução e execuções
│   ├── checkouts.py                cache de checkouts por revisão
│   ├── panel.py                    documento de estado para painéis
│   ├── plugin_ci.py                plugin ecosystem-ci
│   ├── plugin_full.py              modo completo do plugin ecosystem-ci
│   ├── approvals.py                aprovação por uma pessoa
│   ├── store.py                    base de dados local e diário
│   ├── schema.py                   verificador de contratos
│   ├── redaction.py                ocultação de segredos
│   └── i18n.py                     textos em oito idiomas
├── contracts/                      contratos JSON Schema
├── tests/                          testes automáticos
├── configs/                        configuração de exemplo, tudo fechado
├── docs/                           documentos do projeto
├── tools/                          ferramentas do projeto e verificações da CI
├── images/                         Multimédia e ícones da aplicação
├── .github/                        fluxo de CI e modelos de problemas
├── build.sh / build.bat            venv + instalação editável + verificação de compilação + testes
├── run.sh / run.bat                Reencaminha um comando real da CLI
├── bump_version.py                 Subida de versão ao estilo conta-quilómetros (executada só pelo comando `bump` explícito)
├── bump_manifest_version.py        Sincroniza a versão do hydra-umc.project.json com a nativa (--sync)
├── CHANGELOG.md                    o que mudou em cada versão
├── build-test.sh                   verificação de compilação sem alterações
├── hydra-umc.project.json          manifesto: versão, maturidade, família
├── pyproject.toml                  metadados do pacote
└── test.sh                         executa os testes
```

</details>

## 🗺️ Roteiro e limites conhecidos

**Limites conhecidos hoje**

Esta versão inclui as cinco peças acima. O que ainda não existe:

- **Isolamento de uma execução.** Uma receita corre com os direitos do utilizador que executa o nó, com uma lista de programas permitidos, um ambiente mínimo e limites de tempo e de saída; ainda não há uma sandbox (contentor, espaços de nomes). Uma pessoa deve ler a receita antes de a aprovar.
- **Uma aprovação mais forte.** Uma aprovação é um registo na base de dados local feito num terminal; não está assinada com uma chave de quem aprova.
- **O painel do outro lado.** O documento de estado é um contrato e um ficheiro; o `HYDRA-UMC-DASHBOARD-AI` e o `HYDRA-UMC-STUDIO` ainda não o mostram, e a forma como o ficheiro lhes chega (um túnel autenticado) é decisão deles.
- **Um ciclo de trabalho.** Os casos, as receitas e os checkouts usam-se com comandos; nada tira um caso da fila e o trabalha sozinho, de propósito.
- **Uma execução num anfitrião de desenvolvimento real.** O nó só foi testado num computador com repositórios git locais.

## 🌍 Idiomas

Este README e os documentos do repositório existem em oito idiomas: inglês, espanhol, alemão, francês, italiano, japonês, chinês e português (Portugal). São escritos em conjunto e a CI verifica que os oito ficheiros têm as mesmas secções e as mesmas ligações. Este repositório não tem ecrã nem catálogo de mensagens próprios, por isso não há textos de interface para traduzir.

## 🔗 Projetos relacionados

Este projeto faz parte do ecossistema de robótica HYDRA-UMC do mesmo autor (JuanenRac / Electro Hobby 3D). Vale a pena conhecê-los, porque um pedido pode ser, na verdade, sobre um destes e não sobre este repositório.

**Diretamente relacionados**
- **[HYDRA-UMC-LOCAL-TECHNICIAN](https://github.com/JuanenRac/HYDRA-UMC-LOCAL-TECHNICIAN)** — produz os pacotes de provas que este nó lê; o nó apenas os verifica e guarda, nunca os altera nem executa o que dizem.
- **[HYDRA-UMC-DEV-SERVER](https://github.com/JuanenRac/HYDRA-UMC-DEV-SERVER)** — anfitrião de desenvolvimento reproduzível com uma fila de tarefas duradoura; este nó é o lugar mais leve onde uma falha é estudada e reproduzida depois de uma pessoa aprovar cada execução.
- **[HYDRA-UMC-OPS-AGENT](https://github.com/JuanenRac/HYDRA-UMC-OPS-AGENT)** — é responsável pelo ciclo de vida dos incidentes de manutenção (provas, diagnóstico, alteração aprovada por uma pessoa, implementação canary, verificação); este nó fornece o passo de reprodução e nunca aprova uma alteração.
- **[HYDRA-UMC-SDK](https://github.com/JuanenRac/HYDRA-UMC-SDK)** — os contratos partilhados: o resultado de cenário de cada execução de reprodução segue o seu esquema e o SDK calcula o veredito de um par antes e depois.

**Também fazem parte do ecossistema**

*Hardware e plataforma centrais*
- **[HYDRA-UMC](https://github.com/JuanenRac/HYDRA-UMC)** — o desenho da placa-mãe do braço robótico: anfitrião CM5 + STM32H745 de dois núcleos, pensado para orquestrar até 8 braços de ferramenta por CAN-OTA/SPI-OTA (firmware numa fase inicial; ainda sem placa montada).
- **[HYDRA-UMC-OS](https://github.com/JuanenRac/HYDRA-UMC-OS)** — camada de produto reproduzível do Raspberry Pi OS para o CM5: agente só de leitura, configuração/perfis validados, aprovisionamento Wi-Fi de primeiro contacto.

*Backend central e clientes*
- **[HYDRA-UMC-SERVER](https://github.com/JuanenRac/HYDRA-UMC-SERVER)** — o back-end headless real (REST/WebSocket) com que todos os clientes de controlo realmente comunicam.
- **[HYDRA-UMC-STUDIO](https://github.com/JuanenRac/HYDRA-UMC-STUDIO)** — painel web de controlo com visualização 3D em tempo real de vários robôs.
- **[HYDRA-UMC-SUITE](https://github.com/JuanenRac/HYDRA-UMC-SUITE)** — centro de comando de enxame para desktop (PySide6) para vários servidores ao mesmo tempo.
- **[HYDRA-UMC-ANDROID-CONTROL](https://github.com/JuanenRac/HYDRA-UMC-ANDROID-CONTROL)** — aplicação Android nativa de controlo, com início de sessão biométrico e um companheiro Wear OS emparelhado.
- **[HYDRA-UMC-IOS-CONTROL](https://github.com/JuanenRac/HYDRA-UMC-IOS-CONTROL)** — aplicação de controlo para iOS/iPadOS (Flutter) com sincronização WebSocket em tempo real.
- **[HYDRA-UMC-DSI](https://github.com/JuanenRac/HYDRA-UMC-DSI)** — interface tátil nativa para o ecrã tátil DSI de 7" integrado, executada no próprio CM5.
- **[HYDRA-UMC-EDITOR-URDF](https://github.com/JuanenRac/HYDRA-UMC-EDITOR-URDF)** — criador/editor gráfico de URDF para desktop que envia os modelos concluídos para o catálogo do STUDIO.
- **[HYDRA-UMC-EDITOR-STL](https://github.com/JuanenRac/HYDRA-UMC-EDITOR-STL)** — editor de modelos STL para desktop que transforma/substitui/remove/adiciona peças reais no mesmo catálogo de modelos que o HYDRA-UMC-EDITOR-URDF também edita.
- **[HYDRA-UMC-BRIDGE-AMR](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-AMR)** — fronteira de coordenação para frotas AGV/AMR através de um publicador MQTT VDA 5050 (testado apenas contra uma frota emulada).
- **[HYDRA-UMC-BRIDGE-CNC](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-CNC)** — coordenador de células CNC de alto nível com acesso ao estado GRBL e aos bytes de controlo (testado apenas contra um emulador).
- **[HYDRA-UMC-BRIDGE-DROIDS](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-DROIDS)** — fronteira de coordenação para droides com patas/humanoides, com um emissor de comandos para o Boston Dynamics Spot (testado apenas contra um emulador).
- **[HYDRA-UMC-BRIDGE-LASER](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-LASER)** — coordenador de células laser que lê 3 sinais GPIO (chave, caixa e interlock) (testado apenas contra um chip simulado; não pode armar nem disparar um laser).
- **[HYDRA-UMC-BRIDGE-OPENPNP](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-OPENPNP)** — coordenador seguro de fluxo de placa de alto nível para pick-and-place com OpenPnP.
- **[HYDRA-UMC-BRIDGE-PRINTER3D](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-PRINTER3D)** — fronteira de coordenação segura para impressoras 3D Moonraker/Klipper, com comandos de trabalho reais protegidos por portas.
- **[HYDRA-UMC-BRIDGE-ROS2](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-ROS2)** — coordenador com um transporte ROS 2 baseado em rclpy importado sob demanda (ainda não executado contra uma instalação ROS 2).
- **[HYDRA-UMC-BRIDGE-UAV](https://github.com/JuanenRac/HYDRA-UMC-BRIDGE-UAV)** — fronteira de coordenação para UAV com câmara, com um emissor de comandos MAVLink (testado apenas contra um emulador).

*Plataforma de ferramentas URTC*
- **[URTC](https://github.com/JuanenRac/URTC)** — firmware da placa física Universal Robot Tool Controller, mais de 25 perfis de ferramenta por barramento CAN.
- **[URTC-FLASHER](https://github.com/JuanenRac/URTC-FLASHER)** — ferramenta gráfica de gravação para desktop das placas URTC, por CAN-OTA e também SWD/JTAG de chip completo.
- **[URTC-TESTER](https://github.com/JuanenRac/URTC-TESTER)** — ferramenta de diagnóstico CAN em tempo real para desktop das placas URTC, com um painel por perfil de ferramenta.
- **[URTC-WEB-STUDIO](https://github.com/JuanenRac/URTC-WEB-STUDIO)** — alternativa no navegador ao URTC-TESTER através da Web Serial API, sem instalação local.
- **[URTC-GATEWAY](https://github.com/JuanenRac/URTC-GATEWAY)** — gateway à frente do barramento CAN do URTC: lista de identificadores permitidos, limite de taxa e chave de sessão; software testado num computador, ainda não num barramento real.

*Nó de IA de visão (Hailo-8)*
- **[HYDRA-UMC-VISION-NODE](https://github.com/JuanenRac/HYDRA-UMC-VISION-NODE)** — centro de integração do pipeline de visão Hailo-8, com uma verificação real de prontidão de hardware por fase.
- **[HYDRA-UMC-DETECTION-HEF](https://github.com/JuanenRac/HYDRA-UMC-DETECTION-HEF)** — registo real de modelos compilados com verificação segura de carga por arquitetura Hailo e soma de verificação.
- **[HYDRA-UMC-VISION-STREAMER](https://github.com/JuanenRac/HYDRA-UMC-VISION-STREAMER)** — pipeline GStreamer real e gerador de configuração MediaMTX com uma fronteira de integração HailoRT real.
- **[HYDRA-UMC-VISUAL-SERVOING-API](https://github.com/JuanenRac/HYDRA-UMC-VISUAL-SERVOING-API)** — lei de correção de servovisão baseada em posição com autorização condicionada ao estado da zona; ainda sem estimativa de pose por câmara.
- **[HYDRA-UMC-SAFETY-ZONES](https://github.com/JuanenRac/HYDRA-UMC-SAFETY-ZONES)** — lógica v0 de violação de zonas, atualidade da calibração e pedido de E-STOP que lê as posições dos objetos de um ficheiro; nenhum detetor a alimenta e ainda não há E-STOP físico ligado.

*Nó de IA cognitiva (Hailo-10)*
- **[HYDRA-UMC-COGNITIVE-NODE](https://github.com/JuanenRac/HYDRA-UMC-COGNITIVE-NODE)** — centro de integração do pipeline cognitivo do Hailo-10 (orquestração de LLM/VLA/voz).
- **[HYDRA-UMC-VLA-ENGINE](https://github.com/JuanenRac/HYDRA-UMC-VLA-ENGINE)** — codificação/descodificação real de tokens de ação e geração de trajetórias para um modelo Visão-Linguagem-Ação.
- **[HYDRA-UMC-VOICE-UI](https://github.com/JuanenRac/HYDRA-UMC-VOICE-UI)** — front-end de voz real (VAD + analisador de intenções) com um relé para o Watch limitado e sujeito a confirmação - não tem superfície de notificação de saída, por isso este projeto publica os seus eventos de incidente no broker do ecossistema.
- **[HYDRA-UMC-SEMANTIC-PLANNER](https://github.com/JuanenRac/HYDRA-UMC-SEMANTIC-PLANNER)** — decomposição real de tarefas baseada em regras e recuperação semântica de erros sobre os códigos de erro do MCU.
- **[HYDRA-UMC-DOCS-QA](https://github.com/JuanenRac/HYDRA-UMC-DOCS-QA)** — pesquisa real de documentos TF-IDF só com a biblioteca padrão sobre a documentação Markdown deste ecossistema.

*Orquestração e enxame*
- **[HYDRA-UMC-ORCHESTRATOR](https://github.com/JuanenRac/HYDRA-UMC-ORCHESTRATOR)** — centro de integração com um contrato real de relatório de saúde gRPC/Protobuf e uma máquina de estados de missões.
- **[HYDRA-UMC-JOB-DISPATCHER](https://github.com/JuanenRac/HYDRA-UMC-JOB-DISPATCHER)** — fila real de trabalhos por prioridade com deduplicação, sobre uma API HTTP real.
- **[HYDRA-UMC-PATH-PLANNER-3D](https://github.com/JuanenRac/HYDRA-UMC-PATH-PLANNER-3D)** — planeador real de trajetórias 3D baseado em RRT com validação real de colisões com obstáculos e espaço de trabalho.
- **[HYDRA-UMC-SWARM-SYNC](https://github.com/JuanenRac/HYDRA-UMC-SWARM-SYNC)** — sincronização real de estado CRDT LWW-Element-Map, testada por propriedades para a convergência de várias células.
- **[HYDRA-UMC-NODE-HEALING](https://github.com/JuanenRac/HYDRA-UMC-NODE-HEALING)** — um vigilante real de saúde da frota por gRPC, com repetição/recuo próprios e deteção de identidade incoerente.

*Gémeo digital e simulação*
- **[HYDRA-UMC-TWIN](https://github.com/JuanenRac/HYDRA-UMC-TWIN)** — centro de integração do motor de gémeo digital, com um contrato real de sincronização de compatibilidade de versões.
- **[HYDRA-UMC-HIL-BRIDGE](https://github.com/JuanenRac/HYDRA-UMC-HIL-BRIDGE)** — encaminhador hardware-in-the-loop com um interlock de software de colisão entre a simulação e o hardware real (testado sem hardware real).
- **[HYDRA-UMC-PHYSICS-REPLICA](https://github.com/JuanenRac/HYDRA-UMC-PHYSICS-REPLICA)** — cinemática direta real e validação de limites de juntas sobre um subconjunto real de URDF.
- **[HYDRA-UMC-SYNTHETIC-DATA-GEN](https://github.com/JuanenRac/HYDRA-UMC-SYNTHETIC-DATA-GEN)** — gerador procedural real de cenas 2D com exportação de anotações YOLO/COCO.

*Dados e análise*
- **[HYDRA-UMC-DATALAKE](https://github.com/JuanenRac/HYDRA-UMC-DATALAKE)** — armazém real de séries temporais sobre sqlite3 com uma API HTTP real de ingestão/consulta.
- **[HYDRA-UMC-ANOMALY-DETECTOR](https://github.com/JuanenRac/HYDRA-UMC-ANOMALY-DETECTOR)** — detetor real de anomalias por FFT e linha de base estatística, com monitorização de deriva.
- **[HYDRA-UMC-PRODUCTION-REPORTS](https://github.com/JuanenRac/HYDRA-UMC-PRODUCTION-REPORTS)** — cálculo real de OEE/disponibilidade sobre o histórico do DATALAKE, com exportação CSV reprodutível.
- **[HYDRA-UMC-TELEMETRY-COLLECTOR](https://github.com/JuanenRac/HYDRA-UMC-TELEMETRY-COLLECTOR)** — pipeline real de ingestão CAN/WebSocket para o DATALAKE, com deduplicação por sequência.

*Gateway industrial*
- **[HYDRA-UMC-GATEWAY-INDUSTRIAL](https://github.com/JuanenRac/HYDRA-UMC-GATEWAY-INDUSTRIAL)** — centro de integração que retransmite para protocolos industriais, com uma camada real de lista de comandos permitidos e contrapressão.
- **[HYDRA-UMC-OPCUA-SERVER](https://github.com/JuanenRac/HYDRA-UMC-OPCUA-SERVER)** — espaço de endereços OPC-UA real, verificado com uma sessão de cliente real do protocolo binário.
- **[HYDRA-UMC-MQTT-BROKER](https://github.com/JuanenRac/HYDRA-UMC-MQTT-BROKER)** — broker MQTT real com autenticação opcional por cliente e ACL de tópicos.
- **[HYDRA-UMC-MTCONNECT-ADAPTER](https://github.com/JuanenRac/HYDRA-UMC-MTCONNECT-ADAPTER)** — endpoints XML MTConnect `/probe` e `/current` reais com saída em modo degradado.

*Ferramentas complementares*
- **[HYDRA-UMC-DASHBOARD-AI](https://github.com/JuanenRac/HYDRA-UMC-DASHBOARD-AI)** — painéis de Resumos Inteligentes e Realce de Anomalias sobre o DATALAKE/ANOMALY-DETECTOR, com um recurso estatístico honesto.
- **[HYDRA-UMC-TOOL-CLI](https://github.com/JuanenRac/HYDRA-UMC-TOOL-CLI)** — CLI da frota com um contrato de códigos de saída real e estável, um cliente vivo genuíno da API do HYDRA-UMC-SERVER.
- **[HYDRA-UMC-WATCH](https://github.com/JuanenRac/HYDRA-UMC-WATCH)** — aplicação companheira WearOS com padrões de alerta tátil e um relé de voz para o telemóvel emparelhado (ainda não executada num relógio físico).
- **[HYDRA-UMC-CONNECTOR-HUB](https://github.com/JuanenRac/HYDRA-UMC-CONNECTOR-HUB)** — catálogo de capacidades de adaptadores externos, só GET por desenho.
- **[URTC-SMART-RACK](https://github.com/JuanenRac/URTC-SMART-RACK)** — firmware de um rack de montagem de placas com descodificação real do ID da ferramenta e lógica de pré-aquecimento Smart Idle.
- **[URTC-VISION-TOOL](https://github.com/JuanenRac/URTC-VISION-TOOL)** — firmware mais um companheiro de visão em Python real para uma cabeça de ferramenta de inspeção térmica/RGB.
- **[HYDRA-UMC-UPDATER](https://github.com/JuanenRac/HYDRA-UMC-UPDATER)** — ferramenta administrativa de desktop que descobre, clona e atualiza todos os repositórios deste ecossistema.
- **[HYDRA-UMC-OS-REBUILDER](https://github.com/JuanenRac/HYDRA-UMC-OS-REBUILDER)** — constrói uma imagem nova do CM5 a partir do código-fonte, outro irmão de «Operações do ecossistema».

## 📚 Documentação

Onde ler mais:

* **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — as peças, o fluxo de um incidente e onde o nó para.
* **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** — cada interruptor e cada valor ajustável do ficheiro de configuração.
* **[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)** — cada comando, os códigos de saída e a forma de uma receita.
* **[docs/SECURITY_MODEL.md](docs/SECURITY_MODEL.md)** — as regras que o nó cumpre e o que não cobre.
* **[docs/PANEL_CONTRACT.md](docs/PANEL_CONTRACT.md)** — o documento de estado para painéis e estúdios.
* [Base de segurança do ecossistema](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/SECURITY_BASELINE.md)
* [Modelo de ameaças do ecossistema](https://github.com/JuanenRac/HYDRA-UMC-DOCS/blob/main/docs/THREAT_MODEL.md)
* [Registo de alterações deste repositório](CHANGELOG.md)
* [Licença deste repositório](LICENSE.md)

## 🤝 Contribuir e comunidade

* Antes de um pull request execute `HYDRA_UMC_CI=1 py -3 tools/ci_validate.py` (ou `HYDRA_UMC_CI=1 python3 tools/ci_validate.py`): tem de imprimir `CI_VALIDATION=PASS`. Não execute `build.sh` nem `build.bat` para esta verificação; compilar não é verificar.
* Os oito README são escritos a partir de uma única fonte em HYDRA-UMC-DOCS; não os edite à mão. Altere a fonte e escreva-os de novo com `tools/make_readmes.py`.
* Não afirme num README o que não foi executado: diga «simulado» ou «não testado em hardware» quando for a verdade.
* Consulte [CONTRIBUTING.md](CONTRIBUTING.md), o [código de conduta](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md) e [SUPPORT.md](SUPPORT.md).

## 👤 AUTOR

**JuanenRac (Electro Hobby 3D)** · electrohobby3d@gmail.com

## 📜 LICENÇA

GPL-3.0-or-later - [LICENSE](LICENSE).
