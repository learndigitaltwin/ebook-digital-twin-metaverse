using UnityEngine;

/// <summary>
/// Detecta a passagem de caixas por um sensor da esteira.
/// Este script deve ficar no GameObject que possui o BoxCollider do sensor.
/// </summary>
[RequireComponent(typeof(BoxCollider))]
public class SensorDaEsteira : MonoBehaviour
{
    [Header("Configuração do sensor")]
    public GerenciadorDeSensores gerenciador;

    [Header("Estado atual")]
    public bool sensorOcupado;

    private int numeroDoSensor;

    // Função chamada pelo Unity quando a cena inicia.
    // O collider precisa ser Trigger para detectar a caixa sem bloquear seu movimento.
    // O numero do sensor vem do nome do objeto: Sensor_1, Sensor_2, Sensor_3 ou Sensor_4.
    private void Awake()
    {
        GetComponent<BoxCollider>().isTrigger = true;

        // Tenta ler o número a partir do nome (Sensor_1 -> 1).
        // Se o objeto tiver outro nome, avisamos no Console em vez de travar a cena.
        if (!int.TryParse(name.Replace("Sensor_", ""), out numeroDoSensor))
        {
            Debug.LogError("Renomeie este objeto para Sensor_1, Sensor_2, Sensor_3 ou Sensor_4. Nome atual: " + name, this);
        }
    }

    // Função chamada automaticamente quando uma caixa entra no sensor.
    // A caixa precisa ter Rigidbody para ser identificada.
    private void OnTriggerEnter(Collider outroCollider)
    {
        Rigidbody caixa = outroCollider.attachedRigidbody;

        if (caixa == null) return;
        if (sensorOcupado) return;

        sensorOcupado = true;

        if (gerenciador != null)
        {
            gerenciador.RegistrarPassagem(numeroDoSensor, caixa);
        }
    }

    // Função chamada automaticamente quando a caixa sai do sensor.
    // Com isso o sensor fica pronto para detectar a próxima caixa.
    private void OnTriggerExit(Collider outroCollider)
    {
        Rigidbody caixa = outroCollider.attachedRigidbody;

        if (caixa == null) return;

        sensorOcupado = false;
    }
}
