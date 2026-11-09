using System;
using UnityEngine;

/// <summary>
/// Guarda as informações gerais dos sensores da esteira.
/// Este script deve ficar em um GameObject vazio da cena.
/// </summary>
public class GerenciadorDeSensores : MonoBehaviour
{
    [Header("Total de leituras")]
    public int totalEntrada;
    public int totalPontoA;
    public int totalPontoB;
    public int totalPontoC;

    [Header("Últimas leituras")]
    public string ultimaCaixaEntrada;
    public string ultimaCaixaPontoA;
    public string ultimaCaixaPontoB;
    public string ultimaCaixaPontoC;

    public string ultimoEvento;
    public string ultimaDataHora;

    [Header("Cliente do dashboard web")]
    public ClienteDashboardWeb clienteDashboard;

    private int proximoNumeroDaCaixa = 1;

    // Função chamada pelo SensorDaEsteira quando uma caixa entra em um sensor.
    // O número do sensor define se a caixa entrou no processo ou chegou em um estágio.
    public void RegistrarPassagem(int numeroDoSensor, Rigidbody caixa)
    {
        if (caixa == null) return;

        string nomeDaCaixa = ObterNomeDaCaixa(caixa);

        if (numeroDoSensor == 1)
        {
            totalEntrada++;
            ultimaCaixaEntrada = nomeDaCaixa;
            RegistrarEvento(nomeDaCaixa, "Sensor_1", "Entrada do processo", totalEntrada);
        }
        else if (numeroDoSensor == 2)
        {
            totalPontoA++;
            ultimaCaixaPontoA = nomeDaCaixa;
            RegistrarEvento(nomeDaCaixa, "Sensor_2", "Ponto A - pintura de base", totalPontoA);
        }
        else if (numeroDoSensor == 3)
        {
            totalPontoB++;
            ultimaCaixaPontoB = nomeDaCaixa;
            RegistrarEvento(nomeDaCaixa, "Sensor_3", "Ponto B - tinta de acabamento", totalPontoB);
        }
        else if (numeroDoSensor == 4)
        {
            totalPontoC++;
            ultimaCaixaPontoC = nomeDaCaixa;
            RegistrarEvento(nomeDaCaixa, "Sensor_4", "Ponto C - verniz protetor", totalPontoC);
        }
    }

    // Função que cria um nome simples para cada caixa quando ela entra no processo.
    // Exemplo: Caixa 1, Caixa 2, Caixa 3...
    private string ObterNomeDaCaixa(Rigidbody caixa)
    {
        if (!caixa.name.StartsWith("Caixa "))
        {
            caixa.name = "Caixa " + proximoNumeroDaCaixa;
            proximoNumeroDaCaixa++;
        }

        return caixa.name;
    }

    // Função que registra a leitura no Inspector e no Console.
    private void RegistrarEvento(string caixa, string sensor, string etapa, int totalNoSensor)
    {
        ultimaDataHora = DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss");
        ultimoEvento = caixa + " passou pelo " + sensor + " - " + etapa;

        Debug.Log(
            ultimoEvento +
            " | Data/hora: " + ultimaDataHora +
            " | Tempo de simulação: " + Time.time.ToString("F2") + "s" +
            " | Total neste sensor: " + totalNoSensor,
            this
        );

        if (clienteDashboard != null)
        {
            clienteDashboard.EnviarEvento("sensor", sensor, caixa, etapa, ultimoEvento);
        }
    }

    // Função util para zerar os dados durante os testes.
    [ContextMenu("Zerar dados dos sensores")]
    public void ZerarDadosDosSensores()
    {
        totalEntrada = 0;
        totalPontoA = 0;
        totalPontoB = 0;
        totalPontoC = 0;

        ultimaCaixaEntrada = "";
        ultimaCaixaPontoA = "";
        ultimaCaixaPontoB = "";
        ultimaCaixaPontoC = "";

        ultimoEvento = "";
        ultimaDataHora = "";
        proximoNumeroDaCaixa = 1;
    }
}
