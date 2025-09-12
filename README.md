# Growdevice

## Descrição

Aplicação para rodar em um Raspberry PI 3B através da AWS IoT Core, utilizando a sdk V1 da própria AWS.
Essa aplicação utilizava uma Instância AWS EC2, onde era possível utilizar um túnel SSH através dessa instância, mas atualmente essa instância não está mais habilitada.
Nessa aplicação funciona a leitura de um sensor Termohigrômetro DHT22, a controlar 1 lâmpada de forma temporizada ou manual, além de LED RGB indicador de status e conexão WPS ativada por switch.

## Instalação

A instalação deve ser feita obrigatóriamente em um Raspberry PI 3B, similar ou superior

```bash
pip install -r requirements.txt
```

## PinOut
- Termohigrômetro DHT22: 2
- Lâmpada: 17
- Botão WPS: GND|11
- LED Vermelho: 23
- LED Verde: 10
- LED Azul: 9
- LED Comum: 22

## Uso

utilizar o arquivo config.py para parametrizar os valores para conexão correta

```bash
python main.py
```
e então ativeo WPS no seu roteador, e então o WPS no seu GrowDevice para conectar. 
O LED RGB indica apenas a conexão com internet, não com serviços AWS.
