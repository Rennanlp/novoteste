# Sistema de Aprendizado de Padrões

## Visão Geral

O sistema agora inclui um módulo de **Inteligência Artificial** que aprende automaticamente com as regras manuais criadas pelos usuários. Quanto mais você usar o sistema, mais inteligente ele fica!

## Como Funciona

### 1. Aprendizado Automático
- Quando você cria uma regra manual (ex: `MAX VIGORAN PROMOCIONAL = Max Vigoran Black`), o sistema:
  - Analisa a transformação (de onde vem → para onde vai)
  - Extrai padrões (palavras removidas, adicionadas, substituições)
  - Armazena esses padrões em um banco de dados SQLite

### 2. Sugestões Inteligentes
- Quando um produto aparece sem regra manual correspondente, o sistema:
  - Compara com padrões aprendidos anteriormente
  - Sugere transformações baseadas em similaridade
  - Mostra o nível de confiança de cada sugestão

### 3. Melhoria Contínua
- Quando você **aprova** uma sugestão:
  - O sistema aprende que aquela transformação está correta
  - Aumenta a confiança desse padrão
  - Usará esse padrão mais frequentemente no futuro

- Quando você **rejeita** uma sugestão:
  - O sistema reduz a confiança desse padrão
  - Evita sugerir transformações similares

## Funcionalidades

### Banco de Dados
- **Arquivo**: `learning_patterns.db` (criado automaticamente)
- **Tabelas**:
  - `learned_rules`: Regras aprendidas com histórico de uso
  - `transformation_patterns`: Padrões de transformação extraídos
  - `pending_suggestions`: Sugestões pendentes de aprovação

### Interface

1. **Página de Resultado**:
   - Mostra sugestões da IA para produtos sem regras manuais
   - Permite aprovar/rejeitar sugestões com um clique
   - Exibe nível de confiança de cada sugestão

2. **Página de Padrões Aprendidos** (`/learned_patterns`):
   - Visualiza todos os padrões aprendidos
   - Mostra estatísticas de uso e taxa de sucesso
   - Indica nível de confiança de cada padrão

## Como Usar

1. **Comece usando regras manuais normalmente**
   ```
   MAX VIGORAN PROMOCIONAL = Max Vigoran Black
   TV = TESAO DE VACA
   ```

2. **O sistema aprenderá automaticamente** com cada regra criada

3. **Nas próximas vezes**, quando produtos similares aparecerem, o sistema sugerirá transformações automaticamente

4. **Aprove ou rejeite** as sugestões para melhorar o aprendizado

## Tipos de Padrões Aprendidos

- **Remoção de palavras**: Identifica palavras que são removidas (ex: "PROMOCIONAL")
- **Adição de palavras**: Identifica palavras que são adicionadas (ex: "Black")
- **Substituições**: Identifica substituições de palavras similares
- **Normalização**: Aprende padrões de capitalização e formatação

## Exemplo de Uso

1. Você cria a regra: `MAX VIGORAN PROMOCIONAL = Max Vigoran Black`
2. O sistema aprende:
   - Remove "promocional"
   - Adiciona "black"
   - Normaliza para título (primeira letra maiúscula)

3. Quando aparecer `MAX VIGORAN PROMOCIONAL 2`, o sistema sugerirá: `Max Vigoran Black 2`

4. Você aprova a sugestão → O sistema aumenta a confiança desse padrão

## Arquivos do Sistema

- `learning.py`: Módulo principal de aprendizado
- `app.py`: Integração com o Flask
- `templates/resultado.html`: Interface de sugestões
- `templates/learned_patterns.html`: Visualização de padrões
- `learning_patterns.db`: Banco de dados (criado automaticamente)

## Notas Técnicas

- O sistema usa **SQLite** para armazenamento (sem dependências extras)
- Algoritmos de **similaridade textual** para comparação
- **Aprendizado incremental**: Melhora com o tempo
- **Sistema de confiança**: Padrões mais usados têm maior prioridade

