#!/usr/bin/env python3
import sys, json, math, random

# Aggressive-survival heuristic for Mech Royale.
# Pure stdlib, O(n) per tick, no disk/network, deterministic jitter.

class Bot:
    def __init__(self):
        self.tick=0
        self.last_enemy={}
        self.rng=random.Random(24017)

    @staticmethod
    def vec(v, default=(0.0,0.0,0.0)):
        if isinstance(v, dict):
            return (float(v.get('x',0)), float(v.get('y',v.get('z',0))), float(v.get('z',v.get('y',0))))
        if isinstance(v,(list,tuple)) and len(v)>=2:
            return (float(v[0]), float(v[1]), float(v[2] if len(v)>2 else 0))
        return default

    @staticmethod
    def add(a,b): return tuple(a[i]+b[i] for i in range(3))
    @staticmethod
    def sub(a,b): return tuple(a[i]-b[i] for i in range(3))
    @staticmethod
    def mul(a,s): return tuple(x*s for x in a)
    @staticmethod
    def norm(a): return math.sqrt(sum(x*x for x in a))
    @classmethod
    def unit(cls,a):
        n=cls.norm(a); return cls.mul(a,1.0/n) if n>1e-6 else (0,0,0)

    def entities(self, obs, names):
        for n in names:
            x=obs.get(n)
            if isinstance(x,list): return x
        seen=obs.get('visible') or obs.get('vision') or {}
        if isinstance(seen,dict):
            for n in names:
                if isinstance(seen.get(n),list): return seen[n]
        return []

    def decide(self, obs):
        self.tick += 1
        me=obs.get('self') or obs.get('me') or obs.get('player') or {}
        pos=self.vec(me.get('position') or me.get('pos') or obs.get('position'))
        hp=float(me.get('health',me.get('hp',100)) or 0)
        maxhp=float(me.get('max_health',me.get('maxHp',100)) or 100)
        hp_ratio=hp/max(maxhp,1)
        enemies=self.entities(obs,('enemies','mechs','opponents'))
        pickups=self.entities(obs,('pickups','crates','powerups','items'))

        parsed=[]
        for e in enemies:
            if not isinstance(e,dict): continue
            ep=self.vec(e.get('position') or e.get('pos'))
            d=self.norm(self.sub(ep,pos))
            eh=float(e.get('health',e.get('hp',100)) or 100)
            vel=self.vec(e.get('velocity') or e.get('vel'))
            parsed.append((e,ep,d,eh,vel))

        # Target score: finish weak enemies, prefer nearby isolated targets, avoid full-health brawls.
        target=None
        if parsed:
            def score(q):
                e,ep,d,eh,vel=q
                weak=max(0,100-eh)*1.8
                close=max(0,130-d)*0.55
                threat=35 if e.get('aiming_at_me') or e.get('targeting_me') else 0
                return weak+close+threat-d*0.08
            target=max(parsed,key=score)

        # Zone pressure. Accept several plausible protocol spellings.
        zone=obs.get('zone') or obs.get('safe_zone') or {}
        center=self.vec(zone.get('center') or zone.get('position') or pos)
        radius=float(zone.get('radius',zone.get('safe_radius',1e9)) or 1e9)
        outside=self.norm(self.sub(pos,center)) > radius*0.88

        # Candidate-direction minimum-risk movement.
        dirs=[]
        for k in range(16):
            a=2*math.pi*k/16 + 0.17*math.sin(self.tick*0.19)
            dirs.append((math.cos(a),0,math.sin(a)))
        best, bestscore=dirs[0],-1e99
        for dvec in dirs:
            cand=self.add(pos,self.mul(dvec,24))
            s=0.0
            # Closing zone dominates all aggression.
            s -= self.norm(self.sub(cand,center))*(2.8 if outside else 0.18)
            # Avoid crowds and point-blank focus fire.
            for e,ep,dist,eh,vel in parsed:
                cd=self.norm(self.sub(cand,ep))
                s += min(cd,80)*0.22
                if cd<18: s -= (18-cd)*5.0
            # Strafe current target at useful arm-gun range; push weak targets.
            if target:
                e,ep,dist,eh,vel=target
                cd=self.norm(self.sub(cand,ep))
                desired=34 if eh<35 and hp_ratio>0.48 else 58
                s -= abs(cd-desired)*0.7
            # Loot only when safe and not far off course.
            if pickups and (not parsed or min(q[2] for q in parsed)>45):
                nearest=min(pickups,key=lambda p:self.norm(self.sub(self.vec(p.get('position') or p.get('pos')),pos)))
                pp=self.vec(nearest.get('position') or nearest.get('pos'))
                s -= self.norm(self.sub(cand,pp))*0.32
            # deterministic anti-pattern jitter
            s += self.rng.random()*0.03
            if s>bestscore: bestscore,best=s,dvec

        move=self.add(pos,self.mul(best,60))
        aim=self.add(pos,(1,0,0)); fire=False; weapon=None
        if target:
            e,ep,dist,eh,vel=target
            # Lead moving targets. Conservative lead avoids wild misses.
            lead=min(1.15,max(0.05,dist/95.0))
            aim=self.add(ep,self.mul(vel,lead))
            # Fire under broad engagement range. Wrappers usually reject unavailable weapons safely.
            fire=dist<125 and (hp_ratio>0.22 or eh<30)
            available=me.get('weapons') or obs.get('weapons') or []
            names=[str(w.get('name',w.get('type','')) if isinstance(w,dict) else w).lower() for w in available]
            if dist>75 and any('mortar' in n for n in names): weapon='mortar'
            elif dist>52 and any('laser' in n for n in names): weapon='laser'
            elif dist<28 and any('light' in n for n in names): weapon='lightning'
            else: weapon='arm'

        # Canonical action. If the official starter uses a wrapper, map these four values there.
        action={'move':{'x':move[0],'y':move[1],'z':move[2]},
                'aim':{'x':aim[0],'y':aim[1],'z':aim[2]},
                'fire':bool(fire)}
        if weapon: action['weapon']=weapon
        return action

def main():
    bot=Bot()
    for line in sys.stdin:
        try:
            msg=json.loads(line)
            obs=msg.get('observation',msg)
            out=bot.decide(obs)
            # Preserve an id/sequence when supplied by the engine.
            for k in ('id','seq','tick'):
                if k in msg: out[k]=msg[k]
            print(json.dumps(out,separators=(',',':')),flush=True)
        except Exception as exc:
            print(json.dumps({'move':{'x':0,'y':0,'z':0},'aim':{'x':1,'y':0,'z':0},'fire':False},separators=(',',':')),flush=True)

if __name__=='__main__': main()
