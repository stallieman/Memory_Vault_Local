# pr_git_info

# 🔄 Pull Requests (PR's) - Beginners Uitleg

## 🤔 Wat is een Pull Request?

Een **Pull Request (PR)** is een manier om je code-wijzigingen aan een project voor te stellen en te vragen of ze gemerged (samengevoegd) mogen worden met de hoofdcode.

### Simpele Analogie 📝
Stel je voor:
- Het project is een **gedeeld document**
- Jij wilt **iets toevoegen of wijzigen**
- In plaats van direct te schrijven in het originele document, maak je een **kopie**
- Je maakt je wijzigingen in die kopie
- Dan vraag je: *"Hé, kijk eens naar mijn wijzigingen. Mogen deze in het originele document?"*

**Dat is een Pull Request!** 🎯

---

## 🎭 De Belangrijkste Spelers

### 1. **De Maker** (Jij)
- Persoon die de code heeft geschreven
- Opent de Pull Request
- Wil wijzigingen toevoegen aan het project

### 2. **De Reviewer(s)**
- Teamleden die je code bekijken
- Geven feedback en suggesties
- Kunnen vragen stellen over je code

### 3. **De Maintainer/Approver**
- Persoon die beslist of PR gemerged wordt
- Vaak een senior developer of project owner
- Heeft finale zeggenschap

---

## 📖 Het PR Verhaal - Van Begin Tot Eind

### Stap 1: Je Hebt Code Geschreven ✍️

Je hebt een nieuwe feature gemaakt of een bug gefixt op een **aparte branch** (bijv. `feature/login-button`).

**Waarom een aparte branch?**
- Je main/master branch blijft schoon en werkend
- Je kunt experimenteren zonder de hoofdcode te breken
- Meerdere mensen kunnen tegelijk aan verschillende features werken

---

### Stap 2: Je Opent een Pull Request 🚀

Je gaat naar GitHub en klikt op **"New Pull Request"** of **"Compare & pull request"**.

**Wat gebeurt er?**
- Je vertelt GitHub: *"Vergelijk mijn branch met de main branch"*
- GitHub laat alle verschillen (changes) zien
- Je schrijft een **beschrijving** van wat je hebt gedaan

---

### Stap 3: Je Schrijft een Goede Beschrijving 📄

Een goede PR beschrijving bevat:

```markdown
## Wat doet deze PR?
Voegt een login knop toe aan de homepage

## Waarom is dit nodig?
Gebruikers kunnen momenteel niet inloggen vanaf de homepage

## Wat heb je veranderd?
- Login button component toegevoegd
- Styling aangepast voor responsiveness
- Unit tests toegevoegd

## Screenshots (optioneel)
[Voeg hier afbeeldingen toe als het visueel is]

## Checklist
- [x] Code werkt lokaal
- [x] Tests toegevoegd
- [x] Documentatie bijgewerkt
```

---

### Stap 4: Review Proces Begint 👀

**Wat gebeurt er nu?**

1. **Reviewers krijgen een notificatie**
   - Ze zien je PR in hun lijst
   - Ze kunnen beginnen met bekijken

2. **Reviewers bekijken je code**
   - Ze lezen door alle wijzigingen
   - Ze testen soms lokaal of het werkt
   - Ze denken na: "Is dit goede code? Kan dit beter?"

3. **Reviewers geven feedback**
   - Via **comments** (opmerkingen)
   - Via **suggestions** (voorgestelde wijzigingen)
   - Via **approve** of **request changes**

---

### Stap 5: Feedback Ontvangen 💬

Je krijgt verschillende soorten feedback:

#### **✅ Approve**
> "Ziet er goed uit! Deze code mag de main branch in."

**Betekenis:** De reviewer is tevreden, geen wijzigingen nodig.

---

#### **💬 Comment** (Opmerking)
> "Waarom heb je gekozen voor een button in plaats van een link?"

**Betekenis:** Een vraag of suggestie, maar niet blokkerend. Je mag zelf beslissen.

---

#### **🔄 Request Changes** (Wijzigingen Vereist)
> "Deze functie moet aangepast worden. De variabele naam is onduidelijk."

**Betekenis:** Er MOET iets veranderd worden voordat de PR gemerged kan worden.

---

#### **💡 Suggestions** (Voorgestelde Code)
```python
# Suggestion from reviewer:
def calculate_total(items):
    return sum(item.price for item in items)
```

**Betekenis:** De reviewer stelt directe code-wijziging voor. Je kunt deze met 1 klik accepteren!

---

### Stap 6: Je Verwerkt de Feedback 🔧

**Wat doe je met feedback?**

1. **Lees alle comments goed door**
   - Begrijp wat er gevraagd wordt
   - Stel vragen als iets niet duidelijk is

2. **Pas je code aan**
   - Maak de gevraagde wijzigingen
   - Commit en push naar dezelfde branch
   - De PR wordt **automatisch bijgewerkt**!

3. **Reageer op comments**
   - *"Goed punt! Heb het aangepast."*
   - *"Bedankt voor de suggestie, toegepast!"*
   - *"Ik heb het zo gedaan omdat X, maar ik kan het ook anders doen?"*

4. **Mark discussions as resolved**
   - Als je een comment hebt verwerkt, klik "Resolve conversation"
   - Houdt overzicht van wat nog open staat

---

### Stap 7: Re-Review (Indien Nodig) 🔁

Als je wijzigingen hebt gemaakt:
- Je vraagt om een **nieuwe review**: *"Ready for another look!"*
- Reviewers bekijken opnieuw
- Dit proces kan een paar keer herhalen

**Dit is normaal!** 🙂 Goede code ontstaat door iteratie en samenwerking.

---

### Stap 8: Approval & Merge! 🎉

**Als alles goed is:**
1. Reviewer(s) geven **Approve** ✅
2. Maintainer klikt op **"Merge Pull Request"**
3. Je code wordt samengevoegd met main branch
4. De branch kan verwijderd worden (optioneel)

**🎊 Gefeliciteerd! Je code is nu onderdeel van het project!**

---

## 🎨 Visuele Flow van een PR

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. Jij schrijft code op feature branch                    │
│           ↓                                                 │
│  2. Jij opent Pull Request                                  │
│           ↓                                                 │
│  3. Reviewers bekijken je code                              │
│           ↓                                                 │
│  4. Feedback ontvangen (Comments/Changes/Approve)           │
│           ↓                                                 │
│  5. Jij past code aan op basis van feedback                │
│           ↓                                                 │
│  6. Reviewers checken opnieuw                               │
│           ↓                                                 │
│  7. ✅ Approved!                                            │
│           ↓                                                 │
│  8. 🎉 Merge naar main branch                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Waarom Pull Requests?

### ✅ Voordelen

#### **1. Code Quality** (Kwaliteit)
- Meerdere ogen zien meer dan twee
- Fouten worden gevonden voordat ze in productie komen
- Best practices worden gedeeld en geleerd

#### **2. Knowledge Sharing** (Kennis Delen)
- Teamleden leren van elkaars code
- Junior developers leren van senior reviews
- Iedereen weet wat er in het project gebeurt

#### **3. Documentatie**
- PR's zijn een geschiedenis van beslissingen
- Je kunt later terugkijken: "Waarom is dit zo gedaan?"
- Discussies blijven bewaard

#### **4. Samenwerking**
- Team werkt samen aan oplossingen
- Verschillende perspectieven leiden tot betere code
- Gevoel van gezamenlijk eigenaarschap

#### **5. Veiligheid**
- Bugs worden gevangen voordat ze live gaan
- Breaking changes worden vroeg gespot
- Main branch blijft altijd werkend

---

## 💡 PR Best Practices

### ✅ Voor de PR Maker

#### **1. Houd PR's Klein**
❌ **Slecht:** 50 files gewijzigd, 2000 regels code
✅ **Goed:** 5 files gewijzigd, 200 regels code

**Waarom?** Kleine PR's zijn:
- Makkelijker te reviewen
- Sneller gemerged
- Minder risico op bugs

---

#### **2. Schrijf Duidelijke Titels**
❌ **Slecht:** "Update stuff"
✅ **Goed:** "feat: Add user authentication with JWT"

**Format:** `type: description`
- `feat:` - nieuwe feature
- `fix:` - bug fix
- `docs:` - documentatie
- `refactor:` - code verbetering zonder functionaliteit te wijzigen
- `test:` - tests toevoegen

---

#### **3. Goede Beschrijving Schrijven**
Beantwoord deze vragen:
- **Wat** heb je gedaan?
- **Waarom** was dit nodig?
- **Hoe** heb je het opgelost?
- Zijn er **trade-offs** of **beslissingen** die reviewers moeten weten?

---

#### **4. Test Je Code Eerst**
Voordat je PR opent:
- ✅ Code werkt lokaal
- ✅ Tests draaien (en slagen)
- ✅ Geen console errors
- ✅ Documentatie bijgewerkt indien nodig

---

#### **5. Wees Open voor Feedback**
- Neem feedback niet persoonlijk
- Het gaat om de code, niet om jou
- Vraag om verduidelijking als je iets niet begrijpt
- Bedank reviewers voor hun tijd

---

### ✅ Voor Reviewers

#### **1. Wees Constructief**
❌ **Slecht:** "Deze code is verschrikkelijk"
✅ **Goed:** "Deze functie kan simpeler. Wat denk je van deze aanpak?"

---

#### **2. Vraag "Waarom"**
In plaats van te zeggen "dit is fout", vraag:
- "Waarom heb je gekozen voor deze aanpak?"
- "Heb je andere oplossingen overwogen?"

Misschien had de developer een goede reden!

---

#### **3. Geef Concrete Suggesties**
❌ **Slecht:** "Deze code moet beter"
✅ **Goed:** "Overweeg deze refactor: [code suggestion]"

---

#### **4. Balans Tussen Kritisch en Positief**
- Wijs op problemen, maar ook op goede dingen!
- "Mooie oplossing voor X! Bij Y zou ik..."

---

## 🔍 Waar Reviewers Op Letten

### **1. Functionaliteit** ⚙️
- Doet de code wat het moet doen?
- Zijn er edge cases vergeten?
- Werkt het in alle scenario's?

### **2. Leesbaarheid** 📖
- Is de code makkelijk te begrijpen?
- Zijn variabelen duidelijk benoemd?
- Is er voldoende commentaar (waar nodig)?

### **3. Performance** ⚡
- Is de code efficiënt?
- Geen onnodige loops of database calls?
- Schaalt het bij veel data?

### **4. Security** 🔒
- Geen hardcoded passwords of API keys?
- Input validatie aanwezig?
- Geen SQL injection risico's?

### **5. Tests** 🧪
- Zijn er tests voor nieuwe code?
- Dekken tests de belangrijkste scenarios?
- Slagen alle tests?

### **6. Style & Conventions** 🎨
- Volgt het de code style van het project?
- Consistent met bestaande code?
- Naamgeving volgens conventies?

---

## 🎭 PR Statussen - Wat Betekenen Ze?

### **🟡 Open**
PR is aangemaakt en wacht op review of wijzigingen.

### **🟣 Draft** (Concept)
PR is nog niet klaar voor review. Gebruik dit voor work-in-progress om early feedback te krijgen.

### **🟢 Approved**
Reviewer(s) hebben goedkeuring gegeven. Klaar voor merge!

### **🔴 Changes Requested**
Reviewer wil dat je iets aanpast voordat merge mogelijk is.

### **⚫ Closed**
PR is gesloten zonder te mergen. Dit gebeurt als:
- De feature is niet meer nodig
- Er is een betere oplossing gevonden
- De PR is te oud/outdated

### **🟣 Merged**
PR is succesvol gemerged in de main branch. Je code is nu live!

---

## 🛠️ Praktisch Voorbeeld - Stap voor Stap

### Scenario: Je voegt een "Dark Mode" feature toe

#### **Week 1 - Maandag**
```
Je: Ik ga dark mode toevoegen!
    → Maakt branch: feature/dark-mode
    → Schrijft code voor 3 dagen
```

#### **Week 1 - Donderdag**
```
Je: Code is klaar! Tijd voor PR
    → Opent PR: "feat: Add dark mode toggle"
    → Beschrijving: "Users can now switch between light/dark theme"
    → Assigned: @senior-dev en @designer voor review
```

#### **Week 1 - Vrijdag**
```
@senior-dev: "Nice! Maar de toggle button moet ook keyboard accessible zijn"
@designer: "Kleuren zijn goed, maar tekst contrast moet hoger"

Je: "Goed punt! Ga ik aanpassen"
    → Past code aan
    → Pusht wijzigingen (PR update automatisch)
```

#### **Week 2 - Maandag**
```
Je: "Wijzigingen gemaakt, ready for re-review!"

@senior-dev: "Perfect! Approved ✅"
@designer: "Kleuren zijn nu top! Approved ✅"

Maintainer: "Great work team!"
            → Clicked "Merge Pull Request"
            → 🎉 Dark mode is live!
```

---

## 💬 Veelgestelde Vragen

### **Q: Hoe lang moet ik wachten op een review?**
**A:** Verschilt per team. Meestal:
- Kleine PR's: 24-48 uur
- Grote PR's: 3-5 dagen
- Urgent fixes: Binnen een paar uur

Als het lang duurt, mag je vriendelijk een reminder sturen!

---

### **Q: Wat als ik het oneens ben met feedback?**
**A:** Dat is oké! Leg je redenering uit:
- "Ik snap je punt, maar ik koos voor X omdat..."
- "Dat is een goede suggestie! Alternatief zou ook Y kunnen?"

Discussie is gezond. Soms vindt de reviewer jouw punt ook goed!

---

### **Q: Moet ik ALLE feedback verwerken?**
**A:** 
- **Request Changes:** JA, verplicht
- **Comments/Suggestions:** Meestal wel, maar je mag discussiëren
- Als je iets niet doet, leg uit waarom

---

### **Q: Mag ik code reviewen als junior?**
**A:** Absoluut! Je leert er het meeste van. Je hoeft niet alles te begrijpen. Stel vragen:
- "Ik snap dit niet helemaal, kun je uitleggen?"
- "Waarom heb je gekozen voor deze aanpak?"

Senior developers waarderen betrokkenheid!

---

### **Q: Wat als mijn PR conflicts heeft met main?**
**A:** Dit betekent dat main is veranderd sinds jij begon. Je moet je branch "updaten":
1. Pull de laatste main branch
2. Merge main in jouw feature branch
3. Los conflicts op
4. Push weer

De PR wordt dan automatisch bijgewerkt.

---

### **Q: Kan ik een PR weer sluiten/deleten?**
**A:** Ja! Als je besluit dat het niet nodig is of een andere oplossing beter is, klik "Close Pull Request". De code blijft bewaard, maar wordt niet gemerged.

---

## 🎓 Recap - Key Takeaways

1. **PR = Voorstel** om code te mergen
2. **Review proces** zorgt voor kwaliteit
3. **Kleine PR's** zijn beter dan grote
4. **Goede beschrijving** helpt reviewers
5. **Feedback** is bedoeld om te leren, niet om te kritiseren
6. **Iteratie** is normaal - verwacht meerdere review rondes
7. **Samenwerking** maakt code beter

---

## 🚀 Volgende Stappen

Nu je weet hoe PR's werken:
1. **Kijk naar bestaande PR's** in je project
2. **Reviewe een paar PR's** om te zien hoe anderen feedback geven
3. **Maak je eerste eigen PR** - klein beginnen!
4. **Vraag om feedback** op je eerste PR's
5. **Leer van elke review** - het wordt makkelijker!

**Remember:** Elke expert was ooit een beginner. PR's worden makkelijker met oefening! 💪

---

## ✨ Tot Slot

Pull Requests zijn het **hart van teamwork** in software development. Ze zorgen ervoor dat:
- Code altijd door meerdere ogen gaat
- Iedereen blijft leren en groeien
- De codebase van hoge kwaliteit blijft
- Het team samenwerkt aan oplossingen

**Happy coding en reviewing!** 🎉

