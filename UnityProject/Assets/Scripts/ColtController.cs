using UnityEngine;
using System.Collections.Generic;

public class ColtController : MonoBehaviour
{
    [Header("Stats (2026 Meta)")]
    public float baseSpeed = 4.5f;
    public float bulletSpeed = 25f;
    public float baseDamage = 720f;
    
    public float ammo = 3.0f;
    private float reloadTimer = 0f;
    private float reloadMax = 1.3f;
    
    public int superCharge = 0;
    public int hcCharge = 0;
    public bool hcActive = false;
    private float hcTimer = 0f;
    
    [Header("Abilities")]
    public string starPower = "Slick Boots"; 
    public string gadget = "Speedloader";
    public int gadgetUses = 3;
    public bool silverActive = false;
    
    private float sbBuffieTimer = 0f;
    private bool bursting = false;
    private string burstType = "normal";
    private int burstCount = 0;
    private float burstTimer = 0f;
    
    [Header("Mirror Strafing")]
    public bool mirrorStrafing = false;
    public Transform enemyTarget;
    private float targetDist = 0f;
    private Vector3 losVector;
    
    void Update()
    {
        // 1. 상태 계산 (Buffies)
        float curSpeed = baseSpeed;
        float curBSpeed = bulletSpeed;
        float dmgMult = 1.0f;
        
        if (hcActive) { curSpeed *= 1.20f; dmgMult *= 1.05f; }
        if (starPower == "Slick Boots") { 
            curSpeed *= 1.13f; 
            if (sbBuffieTimer > 0) curSpeed *= 1.15f; 
        }
        else if (starPower == "Magnum Special") curBSpeed *= 1.11f;

        if (sbBuffieTimer > 0) sbBuffieTimer -= Time.deltaTime;
        if (hcActive) {
            hcTimer -= Time.deltaTime;
            if (hcTimer <= 0) hcActive = false;
        }

        // 2. 재장전
        if (ammo < 3f && !bursting) {
            reloadTimer -= Time.deltaTime;
            if (reloadTimer <= 0) {
                ammo = Mathf.Min(3.0f, ammo + 1f);
                reloadTimer = hcActive ? reloadMax * 1.1f : reloadMax;
            }
        }
        
        // 3. 에임봇 발사 (Predictive Aim)
        if (bursting) {
            burstTimer -= Time.deltaTime;
            if (burstTimer <= 0) {
                FireBullet(curBSpeed, dmgMult);
            }
        }
    }

    void FireBullet(float bSpeed, float dmgMult)
    {
        Vector3 enemyVel = enemyTarget.GetComponent<EnemyDummy>().velocity;
        Vector3 aimDir = GetPredictiveAim(transform.position, enemyTarget.position, enemyVel, bSpeed);
        
        // 발사 로직 처리 (유니티 프리팹 생성 등)
        if (burstType == "silver") {
            silverActive = false; bursting = false;
        } else if (burstType == "super") {
            burstCount++; burstTimer = 0.05f;
            if (burstCount >= 12) bursting = false;
        } else {
            burstCount++; burstTimer = hcActive ? 0.05f : 0.1f;
            if (burstCount >= 6) bursting = false;
        }
    }

    Vector3 GetPredictiveAim(Vector3 pPos, Vector3 ePos, Vector3 eV, float bSpeed)
    {
        Vector3 d = ePos - pPos;
        float a = eV.sqrMagnitude - bSpeed * bSpeed;
        float b = 2f * Vector3.Dot(d, eV);
        float c = d.sqrMagnitude;
        float t = -1f;

        if (Mathf.Abs(a) < 0.0001f) {
            if (b != 0) t = -c / b;
        } else {
            float desc = b * b - 4 * a * c;
            if (desc >= 0) {
                float t1 = (-b - Mathf.Sqrt(desc)) / (2 * a);
                float t2 = (-b + Mathf.Sqrt(desc)) / (2 * a);
                if (t1 > 0 && t2 > 0) t = Mathf.Min(t1, t2);
                else if (t1 > 0) t = t1;
                else if (t2 > 0) t = t2;
            }
        }
        if (t <= 0) return d.normalized;
        return ((ePos + eV * t) - pPos).normalized;
    }
}
