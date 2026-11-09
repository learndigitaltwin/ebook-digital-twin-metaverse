using System;
using UnityEngine;

/// <summary>
/// Aplica um material na caixa quando ela passa pelo cabeçote de pintura.
/// Este script deve ficar no GameObject Cabecote_N que possui um Collider marcado como Trigger.
/// </summary>
[RequireComponent(typeof(BoxCollider))]
public class CabecoteDePintura : MonoBehaviour
{
    [Header("Material aplicado")]
    public Material materialDaPintura;

    [Header("Dashboard web")]
    public ClienteDashboardWeb clienteDashboard;

    [Header("Última aplicação")]
    public string ultimaCaixaPintada;
    public string ultimaDataHora;
    public int totalCaixasPintadas;

    private int numeroDoCabecote;

    // Função chamada pelo Unity quando a cena inicia.
    // O collider precisa ser Trigger para detectar a caixa sem bloquear seu movimento.
    // O numero do cabeçote vem do nome do objeto: Cabecote_1, Cabecote_2 ou Cabecote_3.
    private void Awake()
    {
        GetComponent<BoxCollider>().isTrigger = true;

        // Tenta ler o número a partir do nome (Cabecote_1 -> 1).
        // Se o objeto tiver outro nome, avisamos no Console em vez de travar a cena.
        if (!int.TryParse(name.Replace("Cabecote_", ""), out numeroDoCabecote))
        {
            Debug.LogError("Renomeie este objeto para Cabecote_1, Cabecote_2 ou Cabecote_3. Nome atual: " + name, this);
        }
    }

    // Função chamada automaticamente quando uma caixa entra na area do cabeçote.
    // Aqui aplicamos o material correspondente ao estágio de pintura.
    private void OnTriggerEnter(Collider outroCollider)
    {
        Rigidbody caixa = outroCollider.attachedRigidbody;

        if (caixa == null) return;
        if (materialDaPintura == null) return;

        Renderer renderizadorDaCaixa = caixa.GetComponentInChildren<Renderer>();

        if (renderizadorDaCaixa == null) return;

        renderizadorDaCaixa.material = materialDaPintura;

        totalCaixasPintadas++;
        ultimaCaixaPintada = caixa.name;
        ultimaDataHora = DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss");

        Debug.Log(
            caixa.name +
            " recebeu " + ObterNomeDoEstagio() +
            " no " + name +
            " em " + ultimaDataHora +
            ". Total pintado neste cabeçote: " + totalCaixasPintadas,
            this
        );

        if (clienteDashboard != null)
        {
            string mensagem = caixa.name + " recebeu " + ObterNomeDoEstagio() + " no " + name;
            clienteDashboard.EnviarEvento("cabecote", name, caixa.name, ObterNomeDoPonto(), mensagem);
        }
    }

    // Função que transforma o número do cabeçote em uma descrição do processo.
    private string ObterNomeDoEstagio()
    {
        if (numeroDoCabecote == 1) return "pintura de base";
        if (numeroDoCabecote == 2) return "tinta de acabamento";
        if (numeroDoCabecote == 3) return "verniz protetor";

        return "material de pintura";
    }

    // Função que informa em qual ponto da esteira este cabeçote trabalha.
    private string ObterNomeDoPonto()
    {
        if (numeroDoCabecote == 1) return "Ponto A - pintura de base";
        if (numeroDoCabecote == 2) return "Ponto B - tinta de acabamento";
        if (numeroDoCabecote == 3) return "Ponto C - verniz protetor";

        return "Ponto de pintura";
    }
}
