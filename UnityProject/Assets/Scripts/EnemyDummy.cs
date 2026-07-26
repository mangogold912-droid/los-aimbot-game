using UnityEngine;

public class EnemyDummy : MonoBehaviour
{
    public float speed = 3.5f;
    public Vector3 targetPos;
    public Vector3 velocity;

    void Start()
    {
        PickNewWaypoint();
    }

    void Update()
    {
        if (Vector3.Distance(transform.position, targetPos) < 1f) {
            PickNewWaypoint();
        }

        Vector3 dir = (targetPos - transform.position).normalized;
        velocity = dir * speed;
        transform.position += velocity * Time.deltaTime;
    }

    void PickNewWaypoint()
    {
        targetPos = new Vector3(Random.Range(-20f, 20f), 0, Random.Range(-20f, 20f));
    }
}
