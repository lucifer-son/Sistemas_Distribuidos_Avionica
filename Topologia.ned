package inet.examples.meu_aviao;

import inet.node.inet.AdhocHost;
import inet.node.tsn.TsnSwitch;
import inet.node.inet.StandardHost;
import inet.node.inet.WirelessHost;
import inet.node.wireless.AccessPoint;
import inet.physicallayer.wireless.common.contract.packetlevel.IRadioMedium;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;

network ArquiteturaAvionica
{
    parameters:
        @display("bgb=950,650;bgu=m");
    submodules:
        configurator: Ipv4NetworkConfigurator {
            @display("p=100,550");
        }
        radioMedium: <default("Ieee80211ScalarRadioMedium")> like IRadioMedium {
            @display("p=100,50");
        }

        // ==========================================================
        // 1. CAMADA DE BORDA: SENSORES FÍSICOS E REDUNDANTES
        // ==========================================================
        // Sensor Cabeado Original
        sensor_freio: StandardHost {
            @display("p=100,380;i=device/sensor");
        }

        // Sensores do Motor Triplamente Redundantes (Geração TMR - WAIC)
        sensor_motor_A: WirelessHost {
            @display("p=100,140;i=device/vessel");
        }
        sensor_motor_B: WirelessHost {
            @display("p=100,220;i=device/vessel");
        }
        sensor_motor_C: WirelessHost {
            @display("p=100,300;i=device/vessel");
        }

        // Sensor Ambiental (Radar Meteorológico - WAIC)
        radar_externo: WirelessHost {
            @display("p=250,80;i=device/radar");
        }

        // Atuador de Saída
        atuador_flap: StandardHost {
            @display("p=849,539;i=device/actuator");
        }

        // ==========================================================
        // 2. INFRAESTRUTURA DE REDE E ROTEAMENTO (AFDX / WAIC)
        // ==========================================================
        // Linha Principal (Canal A)
        tsnSwitch_A: TsnSwitch {
            @display("p=387,349;i=device/switch");
        }
        accessPoint_A: AccessPoint {
            @display("p=386,174;i=device/accesspoint");
        }

        // Linha Redundante (Canal B)
        tsnSwitch_B: TsnSwitch {
            @display("p=388,407;i=device/switch");
        }
        accessPoint_B: AccessPoint {
            @display("p=386,548;i=device/accesspoint");
        }

        // ==========================================================
        // 3. CAMADA LÓGICA E PROCESSAMENTO DISTRIBUÍDO (MQTT)
        // ==========================================================
        // O Broker atua como o nó concentrador (Fusion Place da Rede de Petri)
        broker_mqtt: StandardHost {
            @display("p=580,380;i=device/server");
        }

        // Computadores Lógicos que processam os algoritmos do Artigo
        consenso_votador: StandardHost {
            @display("p=736,264;i=device/cpu");
        }
        automacao_fadec: StandardHost {
            @display("p=727,407;i=device/cpu");
        }

        // Módulos Finais de Visualização e Armazenamento
        computador_voo: StandardHost {
            @display("p=875,379;i=device/laptop");
        }
        caixa_preta: StandardHost {
            @display("p=580,540;i=device/disk");
        }

    connections:
        // Conexões de Infraestrutura (APs conectados aos Switches TSN via AFDX)
        accessPoint_A.ethg++ <--> {  delay = 0.01ms; datarate = 100Mbps; } <--> tsnSwitch_A.ethg++;
        accessPoint_B.ethg++ <--> {  delay = 0.01ms; datarate = 100Mbps; } <--> tsnSwitch_B.ethg++;

        // Redundância Física do Sensor de Freio (Ligado em ambos os Switches)
        sensor_freio.ethg++ <--> {  delay = 0.1ms; datarate = 100Mbps; } <--> tsnSwitch_A.ethg++;
        sensor_freio.ethg++ <--> {  delay = 0.1ms; datarate = 100Mbps; } <--> tsnSwitch_B.ethg++;

        // Encaminhamento dos Switches AFDX para o Middleware Central (Broker)
        tsnSwitch_A.ethg++ <--> {  delay = 0.01ms; datarate = 100Mbps; } <--> broker_mqtt.ethg++;
        tsnSwitch_B.ethg++ <--> {  delay = 0.01ms; datarate = 100Mbps; } <--> broker_mqtt.ethg++;

        // Barramento Lógico de Distribuição (Broker -> Aplicações e Caixa Preta)
        broker_mqtt.ethg++ <--> {  delay = 0.01ms; datarate = 100Mbps; } <--> consenso_votador.ethg++;
        broker_mqtt.ethg++ <--> {  delay = 0.01ms; datarate = 100Mbps; } <--> automacao_fadec.ethg++;
        broker_mqtt.ethg++ <--> {  delay = 0.01ms; datarate = 100Mbps; } <--> caixa_preta.ethg++;

        // Saída dos Computadores de Decisão para o Cockpit do Piloto
        consenso_votador.ethg++ <--> {  delay = 0.01ms; datarate = 100Mbps; } <--> computador_voo.ethg++;
        automacao_fadec.ethg++ <--> {  delay = 0.01ms; datarate = 100Mbps; } <--> computador_voo.ethg++;

        // Comando do Cockpit para os Atuadores Físicos da Asa
        computador_voo.ethg++ <--> {  delay = 0.1ms; datarate = 100Mbps; } <--> atuador_flap.ethg++;
}
