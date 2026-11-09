using UnityEngine;

/// <summary>
/// Move qualquer Rigidbody que esteja encostando na esteira.
/// Use este script no objeto da esteira, junto com um Collider.
/// As caixas precisam ter Rigidbody para serem movidas pela física.
/// </summary>
public class Esteira : MonoBehaviour
{
    [Header("Movimento da esteira")]
    [Tooltip("Direção em que a esteira empurra as caixas. Use X e Z para movimento no chão.")]
    public Vector3 direcao = Vector3.right;

    [Min(0f)]
    [Tooltip("Velocidade horizontal aplicada as caixas enquanto elas estão sobre a esteira.")]
    public float velocidade = 2f;

    [Header("Estabilidade das caixas")]
    [Tooltip("Evita que a caixa tombe para os lados enquanto está sobre a esteira.")]
    public bool travarRotacaoZEnquantoNaEsteira = true;

    private void OnCollisionStay(Collision collision)
    {
        Rigidbody corpoDaCaixa = collision.rigidbody;

        if (corpoDaCaixa == null) return;

        Vector3 direcaoHorizontal = ObterDirecaoHorizontalNormalizada();

        if (direcaoHorizontal == Vector3.zero) return;

        AplicarMovimentoDaEsteira(corpoDaCaixa, direcaoHorizontal);

        if (travarRotacaoZEnquantoNaEsteira)
        {
            corpoDaCaixa.constraints |= RigidbodyConstraints.FreezeRotationZ;
        }
    }

    private void OnCollisionExit(Collision collision)
    {
        if (!travarRotacaoZEnquantoNaEsteira) return;

        Rigidbody corpoDaCaixa = collision.rigidbody;

        if (corpoDaCaixa == null) return;

        corpoDaCaixa.constraints &= ~RigidbodyConstraints.FreezeRotationZ;
    }

    private Vector3 ObterDirecaoHorizontalNormalizada()
    {
        // A esteira deve mover caixas no plano do chão.
        // Por isso ignoramos o eixo Y e preservamos a gravidade.
        Vector3 direcaoHorizontal = new Vector3(direcao.x, 0f, direcao.z);

        if (direcaoHorizontal.sqrMagnitude <= 0f)
        {
            return Vector3.zero;
        }

        return direcaoHorizontal.normalized;
    }

    private void AplicarMovimentoDaEsteira(Rigidbody corpoDaCaixa, Vector3 direcaoHorizontal)
    {
        Vector3 velocidadeAtual = corpoDaCaixa.linearVelocity;
        Vector3 velocidadeDaEsteira = direcaoHorizontal * velocidade;

        // =====================================================================
        //  PRA FAZER 1 (ALUNO) — Mova a caixa aplicando a velocidade da esteira
        // ---------------------------------------------------------------------
        //  Para mover um objeto com física, definimos a velocidade do seu
        //  Rigidbody. Queremos empurrar a caixa nos eixos X e Z (o chão), mas
        //  PRESERVAR o eixo Y (velocidadeAtual.y) para a gravidade continuar
        //  puxando a caixa para baixo normalmente.
        //
        //  Complete a linha abaixo criando um "new Vector3(...)" com:
        //     X = velocidadeDaEsteira.x
        //     Y = velocidadeAtual.y
        //     Z = velocidadeDaEsteira.z
        //
        //  Apague o comentario e escreva o seu codigo (remova a "//" da frente):
        //
        //  corpoDaCaixa.linearVelocity = new Vector3(
        //      velocidadeDaEsteira.x,
        //      velocidadeAtual.y,
        //      velocidadeDaEsteira.z
        //  );
        // =====================================================================
    }
}
