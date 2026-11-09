using UnityEngine;

/// <summary>
/// Cria caixas em um ponto da cena com uma taxa definida em caixas por minuto.
/// Posicione este GameObject onde as caixas devem nascer.
/// </summary>
public class GeradorDeCaixas : MonoBehaviour
{
    [Header("Prefab")]
    [Tooltip("Prefab da caixa que será criada pelo spawn.")]
    public GameObject caixaPrefab;

    [Header("Controle de produção")]
    [Min(0f)]
    [Tooltip("Quantidade de caixas criadas por minuto. Ex.: 30 cria uma caixa a cada 2 segundos.")]
    public float caixasPorMinuto = 30f;

    [Header("Opções")]
    [Tooltip("Quando marcado, o spawn cria caixas automaticamente.")]
    public bool spawnAtivo = true;

    [Min(0f)]
    [Tooltip("Tempo até destruir cada caixa criada. Use 0 para nao destruir automaticamente.")]
    public float destruirDepoisDeSegundos = 0f;

    private float tempoAcumulado;

    private void Start()
    {
        if (PodeCriarCaixa())
        {
            CriarCaixa();
        }
    }

    private void Update()
    {
        if (!PodeCriarCaixa()) return;

        tempoAcumulado += Time.deltaTime;

        float intervaloEntreCaixas = CalcularIntervaloEntreCaixas();

        while (tempoAcumulado >= intervaloEntreCaixas)
        {
            CriarCaixa();
            tempoAcumulado -= intervaloEntreCaixas;
        }
    }

    private bool PodeCriarCaixa()
    {
        return spawnAtivo && caixaPrefab != null && caixasPorMinuto > 0f;
    }

    private float CalcularIntervaloEntreCaixas()
    {
        // =====================================================================
        //  PRA FAZER 2 (ALUNO) — Converta "caixas por minuto" em "segundos por caixa"
        // ---------------------------------------------------------------------
        //  Existem 60 segundos em 1 minuto. Se queremos 'caixasPorMinuto' caixas
        //  a cada 60 segundos, o intervalo (em segundos) entre uma caixa e outra
        //  e:   60 / caixasPorMinuto
        //
        //  Exemplo: 30 caixas por minuto  ->  60 / 30 = 2 segundos entre caixas.
        //
        //  Troque o "return" provisorio abaixo pela conta correta:
        //     return 60f / caixasPorMinuto;
        // =====================================================================
        return 60f; // provisorio: 1 caixa por minuto. Ajuste no PRA FAZER 2.
    }

    private void CriarCaixa()
    {
        GameObject caixa = Instantiate(
            caixaPrefab,
            transform.position,
            transform.rotation
        );

        if (destruirDepoisDeSegundos > 0f)
        {
            Destroy(caixa, destruirDepoisDeSegundos);
        }
    }

    public void AtivarSpawn()
    {
        spawnAtivo = true;
    }

    public void DesativarSpawn()
    {
        spawnAtivo = false;
        tempoAcumulado = 0f;
    }

    public void AlterarCaixasPorMinuto(float novaQuantidade)
    {
        caixasPorMinuto = Mathf.Max(0f, novaQuantidade);
        tempoAcumulado = 0f;
    }
}
