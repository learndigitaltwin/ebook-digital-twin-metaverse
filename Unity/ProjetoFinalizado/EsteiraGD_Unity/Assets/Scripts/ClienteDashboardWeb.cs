using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// Envia eventos simples da cena Unity para o dashboard web local.
/// Coloque este script em um GameObject vazio da cena.
/// </summary>
public class ClienteDashboardWeb : MonoBehaviour
{
    [Header("Servidor local")]
    public string urlDoServidor = "http://localhost:8000/api/eventos";

    [Header("Identificação da fonte")]
    [Tooltip("Nome do ambiente que está enviando os eventos. Aparece no dashboard. " +
             "Nos próximos tutoriais, troque para 'Unreal' ou 'Isaac Sim'.")]
    public string nomeDaFonte = "Unity";

    // Função chamada pelos sensores e cabeçotes para avisar o dashboard.
    public void EnviarEvento(string tipo, string origem, string caixa, string estagio, string mensagem)
    {
        EventoDoDashboard evento = new EventoDoDashboard();
        evento.tipo = tipo;
        evento.origem = origem;
        evento.caixa = caixa;
        evento.estagio = estagio;
        evento.dataHora = DateTime.Now.ToString("dd/MM/yyyy HH:mm:ss");
        evento.tempoSimulacao = Time.time;
        evento.mensagem = mensagem;
        evento.fonte = nomeDaFonte;

        string json = JsonUtility.ToJson(evento);

        StartCoroutine(EnviarJson(json));
    }

    // Coroutine usada pois a requisição HTTP acontece ao longo de alguns frames.
    private IEnumerator EnviarJson(string json)
    {
        byte[] dados = Encoding.UTF8.GetBytes(json);

        using (UnityWebRequest requisicao = new UnityWebRequest(urlDoServidor, "POST"))
        {
            requisicao.uploadHandler = new UploadHandlerRaw(dados);
            requisicao.downloadHandler = new DownloadHandlerBuffer();
            requisicao.SetRequestHeader("Content-Type", "application/json");

            yield return requisicao.SendWebRequest();

            if (requisicao.result != UnityWebRequest.Result.Success)
            {
                Debug.LogWarning("Dashboard web não recebeu o evento: " + requisicao.error, this);
            }
        }
    }

    // Classe simples usada pelo JsonUtility para montar o JSON enviado ao FastAPI.
    [Serializable]
    private class EventoDoDashboard
    {
        public string tipo;
        public string origem;
        public string caixa;
        public string estagio;
        public string dataHora;
        public float tempoSimulacao;
        public string mensagem;
        public string fonte;
    }
}
