# RadarWaze-Maps

Canal público de mapas rodoviários de São Paulo preparados para o Radar Waze.

O aplicativo consulta `https://github.com/lucasnoronha88/RadarWaze-Maps/releases/download/sp-roadmap/latest.json`, compara os hashes instalados e baixa somente conteúdo novo. O ZIP contém vias, restrições e manifesto; o Android constrói seu índice local antes de ativar o mapa.

A rotina verifica a fonte diariamente, às 07:00 UTC, e também pode ser iniciada na aba Actions. Quando a revisão do extrato e a receita não mudam, não baixa nem reconverte o estado inteiro. A publicação usa a credencial temporária do GitHub Actions, restrita a este repositório. Nenhum token pessoal é necessário.

## Fonte e licença dos dados

Dados © OpenStreetMap contributors, disponibilizados sob Open Database License (ODbL) 1.0.

- Fonte: https://download.openstreetmap.fr/extracts/south-america/brazil/southeast/sao-paulo-latest.osm.pbf
- Créditos e licença: https://www.openstreetmap.org/copyright
- Licença ODbL: https://opendatacommons.org/licenses/odbl/1-0/

Os pacotes derivados mantêm essa licença. A fonte original está disponível no endereço acima e os registros transformados estão incluídos no ZIP.

## Estado do roteamento

O formato v2 preserva nós OSM, sentidos e restrições via-node. Restrições condicionais e via-way ainda não são aplicadas integralmente. O campo `routing_safe` permanece falso; o aplicativo mantém o mecanismo de alertas atual enquanto o roteamento é validado em campo.

Este repositório contém somente dados e as rotinas necessárias para prepará-los e publicá-los.
