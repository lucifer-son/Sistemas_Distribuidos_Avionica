package inet.examples.meu_aviao;

import inet.node.tsn.TsnSwitch;
import inet.node.inet.StandardHost;
import inet.node.inet.WirelessHost;
import inet.node.wireless.AccessPoint;
import inet.physicallayer.wireless.common.contract.packetlevel.IRadioMedium;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;

network ArquiteturaAvionica
{
    parameters:
        @display("bgb=900,600");
    submodules:
        configurator: Ipv4NetworkConfigurator {
            @display("p=100,500");
        }
        radioMedium: <default("Ieee80211ScalarRadioMedium")> like IRadioMedium {
            @display("p=100,50");
        }

        // ==========================================
        // CAMADA DE BORDA (SENSORES E ATUADORES)
        // ==========================================
        sensor_freio: StandardHost {
            @display("p=150,380");
        }
        atuador_flap: StandardHost {
            @display("p=749,286");
        }

        // Cluster WAIC (Asas/Motores)
        sensor_WAIC: WirelessHost {
            @display("p=100,160");
        }
        sensor_pressao_motor: WirelessHost {
            @display("p=100,260");
        }

        // Líder do Cluster (Nó de Computação de Borda/Agregador)
        lider_cluster: WirelessHost {
            @display("p=280,210");
        }

        // ==========================================
        // CAMADA DE CORE / GATEWAYS (REDUNDÂNCIA)
        // ==========================================
        // Linha Principal (Canal A)
        tsnSwitch_A: TsnSwitch {
            @display("p=480,380");
        }
        accessPoint_A: AccessPoint {
            @display("p=539,110");
        }

        // Linha Redundante (Canal B)
        tsnSwitch_B: TsnSwitch {
            @display("p=480,480");
        }
        accessPoint_B: AccessPoint {
            @display("p=432,110");
        }

        // ==========================================
        // CAMADA DE PROCESSAMENTO CENTRAL
        // ==========================================
        computador_voo: StandardHost {
            @display("p=750,380"); 
        }

    connections:
        // Ligações do Sensor de Freio aos DOIS Switches (Redundância Física AFDX)
        sensor_freio.ethg++ <--> {  delay = 0.1ms; datarate = 100Mbps; } <--> tsnSwitch_A.ethg++;
        sensor_freio.ethg++ <--> {  delay = 0.1ms; datarate = 100Mbps; } <--> tsnSwitch_B.ethg++;

        // Ligações dos Access Points com seus respectivos Switches TSN
        accessPoint_A.ethg++ <--> {  delay = 0.1ms; datarate = 100Mbps; } <--> tsnSwitch_A.ethg++;
        accessPoint_B.ethg++ <--> {  delay = 0.1ms; datarate = 100Mbps; } <--> tsnSwitch_B.ethg++;

        // Ligações Duplicadas em direção ao Computador de Voo
        tsnSwitch_A.ethg++ <--> {  delay = 0.1ms; datarate = 100Mbps; } <--> computador_voo.ethg++;
        tsnSwitch_B.ethg++ <--> {  delay = 0.1ms; datarate = 100Mbps; } <--> computador_voo.ethg++;

        // Ligação do Switch Principal com o Atuador
        tsnSwitch_A.ethg++ <--> {  delay = 0.1ms; datarate = 100Mbps; } <--> atuador_flap.ethg++;
}
