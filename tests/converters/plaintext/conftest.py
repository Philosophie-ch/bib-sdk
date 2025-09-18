import csv
import io
import pytest
from philoch_bib_sdk.converters.plaintext.bibitem.parser import ParsedBibItemData

# Clean CSV data with problematic entries removed
CSV_BIBITEM_TEST_DATA = r"""_to_do_general,_change_request,entry_type,bibkey,author,_author_ids,editor,_editor_ids,author_ids,options,shorthand,date,pubstate,title,_title_unicode,booktitle,crossref,journal,journal_id,volume,number,pages,eid,series,address,institution,school,publisher,publisher_id,type,edition,note,_issuetitle,_guesteditor,_extra_note,urn,eprint,doi,url,_kw_level1,_kw_level2,_kw_level3,_epoch,_person,_comm_for_profile_bib,_langid,_lang_der,_further_refs,_depends_on,_dltc_num,_spec_interest,_note_perso,_note_stock,_note_status,_num_inwork_coll,_num_inwork,_num_coll,_dltc_copyediting_note,_note_missing,_num_sort
,,@incollection,collins_r:1999a,"Collins, Robin",,,,,,1999,,Eastern Religions,,murray_mj:1999,,,,,182--216,,,,,,,,,,,,,,,,religion,,,,,,,,,30201
,,@incollection,collins_r:2003,"Collins, Robin",,,,,,2003,,Evidence for Fine-Tuning,,manson_na:2003,,,,,178--199,,,,,,,,,,,,,,,,religion,arguments-for-the-existence-of-God,teleological-argument,,,,,,,30202
,,@incollection,collins_r:2004,"Collins, Robin",,,,,,2004,,The Design Argument: Between Science and Metaphysics,,corradini-etal:2004,,,,,140--152,,,,,,,,,,,,,,,,religion,arguments-for-the-existence-of-God,argument-from-design,,,,,,,30203
,,@incollection,collins_r:2006,"Collins, Robin",,,,,,2006,,Contributions from the Philosophy of Science,,clayton_p-simpson:2006,,,,,328--344,,,,,,,,,,,,,,,,religion,science-and-religion,,,,,,,30204
,,@article,collins_r:2008,"Collins, Robin",,,,,,2008,,Modern Physics and the Energy-Conservation Objection to Mind-Body Dualism,,"American Philosophical Quarterly",45,1,31--42,,,,,,,,,,,,,,,,mind/body,dualism,,,,,,,30205
,,@incollection,collins_r:2009a,"Collins, Robin",,,,,,2009,,Divine Action and Evolution,,flint-rea:2009,,,,,241--261,,,,,,,,,,,,,,,,causation,causal-closure,miracles,,,,,,,30207
,,@incollection,collins_r:2011,"Collins, Robin",,,,,,2011,,Prayer and Open Theism: A Participatory\, Co-Creator Model,,hasker-etal:2011,,,,,161--185,,,,,,,,,,,,,,,,religion,theism,open-theism,,,,,,,30208
,,@incollection,collins_r:2011a,"Collins, Robin",,,,,,2011,,The Energy of the Soul,,baker_mc-goetz:2011,,,,,123--137,,,,,,,,,,,,,,,,persons,soul,,,,,,,,,30209
,,@incollection,collins_r:2011b,"Collins, Robin",,,,,,2011,,A Scientific Case for the Soul,,baker_mc-goetz:2011,,,,,222--246,,,,,,,,,,,,,,,,persons,soul,,,,,,,,,30210
,,@incollection,collins_r:2013,"Collins, Robin",,,,,,2013,,The Fine-Tuning Evidence is Convincing,,moreland_jp-etal:2013,,,,,35--46,,,,,,,,,,,,,,,,religion,arguments-for-the-existence-of-God,teleological-argument,,,,,,,,,30212
,,@incollection,collins_r:2013a,"Collins, Robin",,,,,,2013,,The Teleological Argument,,meister_c-copan:2013,,,,,411--421,,,,,,,,,,,,,,,,religion,arguments-for-the-existence-of-God,teleological-argument,,,,,,,,,30213
,,@incollection,collins_r:2013b,"Collins, Robin",,,,,,2013,,Naturalism,,taliaferro-etal:2013,,,,,182--195,,,,,,,,,,,,,,,,metaphilosophy,naturalism,,,,,,,,,30214
,,@incollection,collins_ra:2000,"Collins, Randall",,,,,,2000,,Reflexivity and Social Embeddedness in the History of Ethical Philosophies,,kusch_m:2000,,,,,155--178,,,,,,,,,,,,,,,,metaphilosophy,,,,,,,,,,30215
,,@incollection,collins_ra:2005,"Collins, Randall",,,,,,2005,,The Durkheimian movement in France and in world sociology,,alexander_jc-smith:2005,,,,,101--135,,,,,,,,,,,,,,,,social-sciences,sociology,continental-philosophy,,,,,,,,,30216
,,@article,collins_s-lawfordsmith:2016,"Collins, Stephanie and Lawford-Smith, Holly",,,,,,2016,,Collectives' and Individuals' Obligations: A Parity Argument,,"Canadian Journal of Philosophy",46,1,38--58,,,,,,,,,,,,,,,,action,collective-action,collective-responsibility,,,,,,,,,30217
,,@article,collins_s:2013,"Collins, Stephanie",,,,,,2013,,Collectives' Duties and Collectivization Duties,,"Australasian Journal of Philosophy",91,2,231--248,,,,,,,,,,,,,,,,ethics,,,,,,,,,,30219
,,@article,collins_s:2016,"Collins, Stephanie",,,,,,2016,,The Claims and Duties of Socioeconomic Human Rights,,"The Philosophical Quarterly",66,265,701--722,,,,,,,,,,,,,,,,political-philosophy,rights,human-rights,,,,,,,,,30220
,,@article,collins_s:2017,"Collins, Stephanie",,,,,,2017,,Filling Collective Duty Gaps,,"The Journal of Philosophy",114,11,573--591,,,,,,,,,,,,,,,,ethics,duty,,,,,,,,,30221
,,@article,collins_s:2020,"Collins, Stephanie",,,,,,2020,,How much Can We Ask of Collective Agents?,,"Canadian Journal of Philosophy",50,7,815--831,,,,,,,,,,,,,,,,action,collective-action,,,,,,,,,30223
,,@incollection,collins_s:2020a,"Collins, Stephanie",,,,,,2020,,Collective Responsibility and International Relations,,bazarganforward-tollefsen:2020,,,,,331--346,,,,,,,,,,,,,,,,action,collective-action,collective-responsibility,,,,,,,,,30224
,,@incollection,collinson:2008,"Collinson, Patrick",,,,,,2008,,Antipuritanism,,coffey_j-lim:2008,,,,,19--33,,,,,,,,,,,,,,,,aesthetics,amoralism-in-art,,,,,,,,,30225
,,@incollection,collinsweitz:1982,"Collins Weitz, Margaret",,,,,,1982,,Pastoral Paradoxes,,tymieniecka:1982,,,,,277--290,,,,,,,,,,,,,,,,aesthetics,literary-criticism,,,,,,,,,30226
,,@book,colliotthelene:2011,"Colliot-Th{\'e}l{\`e}ne, Catherine",,,,,,2011,,La d{\'e}mocratie sans ``demos'',La d{\'e}mocratie sans ``demos'',,,,,"Pratiques th{\'e}oriques",Paris,,"Presses Universitaires de France",,,,,,political-philosophy,democracy,,,french,,,,,,,,,,,,,,,,,204465
,,@incollection,collisonblack_rd:1987,"Collison Black, R.D.",,,,,,1987,,Utility,,eatwell-etal:1987,,,,,295--302,,,,,,,,,,,,,,,,decision-theory,preference,utility,,,,,,,,,30227
,,@article,collmarmol:2007,"Coll M{\'a}rmol, Jes{\'u}s Antonio",,,,,,2007,,McDowell's Dogmatic Empiricism,,"Cr{\'{\i}}tica: Revista Hispanoamericana de Filosof{\'{\i}}a",39,116,37--50,,,,,,,,,,,,,,,,,perception,perceptual-content,,,,,,,,,30228
,,@article,collmarmol:2007a,"Coll M{\'a}rmol, Jes{\'u}s Antonio",,,,,,2007,,Conceptual Schemes and Empiricism: What Davidson Saw and McDowell Missed,,"Theoria (San Sebastian), Secunda {\'e}poca",22,2,153--165,,,,,,,10.1387/theoria.465,metaphysics,relativism,conceptual-relativism,,,,,,,,,30229
,,@article,collobert:2002,"Collobert, Catherine",,,,,,2002,,Aristotle's Review of the Presocratics: Is Aristotle Finally a Historian of Philosophy?,,"Journal of the History of Philosophy",40,3,281--295,,,,,,,,,,,,,,,,history-of-philosophy,,ancient-philosophy,Aristotle,,,,,,,,,30230
,,@article,collodel:2016,"Collodel, Matteo",,,,,,2016,,Was Feyerabend a Popperian? Methodological Issues in the History of the Philosophy of Science,,"Studies in History and Philosophy of Science",57,,27--56,,,,,,,,,,,,,,,,science,,,,,,,,,30231
,,@incollection,colman_c-blomme:2021,"Colman, Charlotte and Blomme, Eva",,,,,,2021,,Towards a Strengths-Based Focus in the Criminal Justice System for Drug-Using Offenders,,focquaert_f-etal:2021,,,,,388--403,,,,,,,,,,,,,,,,law,penal-law,punishment,,,,,,,,,30232
,,@incollection,colman_j:1997,"Colman, John",,,,,,1997,,Lockes Theorie der empirischen Erkenntnis (\emph{Essay} IV.i-iii\, vi\, xi-xii),,thiel_u:1997,,,,,197--222,,,,,,,,,,,,,,,,epistemology,,modern-philosophy,Locke,,ngerman,,,,,30233
,,@incollection,colman_j:2003,"Colman, John",,,,,,2003,,Locke's empiricist theory of the law of nature,,anstey:2003,,,,,106--126,,,,,,,,,,,,,,,,causation,laws-of-nature,,modern-philosophy,Locke,,,,,,,30234
,,@article,colmerauer-pique:1985,"Colmerauer, Alain and Pique, Jean Fran{\c{c}}ois",,,,,,1985,,About Natural Logic,,"Logique et Analyse",28,110/111,209--231,,,,,,,,,,,,,,,,logic,natural-deduction,,,,,,,,,30235
,,@article,hitchcock_c:2001a,"Hitchcock, Christopher R.",,,,,,2001,,Review of \citet{pearl_j:2000},,"The Philosophical Review",110,4,639--641,,,,,,,,,,,,,,,,decision-theory,Bayesian-networks,,,,,,,,,69465
,,@article,hitchcock_c:2001b,"Hitchcock, Christopher R.",,,,,,2001,,Causal Generalizations and Good Advice,,"The Monist",84,2,218--241,,,,,,,,,,,,,,,,causation,,,,,,,,,,69466
,,@incollection,hitchcock_c:2002,"Hitchcock, Christopher R.",,,,,,2002,,Probabilistic Causation,"The Stanford Encyclopedia of Philosophy",,,,,,,"Stanford, California",,"The Metaphysics Research Lab, Center for the Study of Language {and} Information",,,,https://plato.stanford.edu/archives/fall2002/entries/causation-probabilistic/,causation,probabilistic-causation,,,,,,,,,69467
,,@incollection,hitchcock_c:2003,"Hitchcock, Christopher R.",,,,,,2003,,Unity and Plurality in the Concept of Causation,,stadler_f:2003,,,,,217--224,,,,,,,,,,,,,,,,causation,,Vienna-Circle,,,,,,,69468
,,@incollection,aagaardolesen:2000,"Aagaard Olesen, Tonny",,,,,,2000,,On Annotating \emph{The Concept of Irony} with Reference to the Editorial History,,cappelorn_nj-etal:2000,,,,,396--421,,,,,,,,,,,,,,,,,history-of-philosophy,,continental-philosophy,Kierkegaard,,,,,,,1
,,@incollection,aagaardolesen:2005,"Aagaard Olesen, Tonny",,,,,,2005,,The Obscure Kierkegaard,,cappelorn_nj-deuser:2005,,,,,314--338,,,,,,,,,,,,,,,,,history-of-philosophy,,continental-philosophy,Kierkegaard,,,,,,,16
,,@incollection,aagaardolesen:2005a,"Aagaard Olesen, Tonny",,,,,,2005,,The Painless Contradiction,,cappelorn_nj-deuser:2005,,,,,339--350,,,,,,,,,,,,,,,,,truth,excluded-middle,(non-)contradiction,continental-philosophy,Kierkegaard,,,,,,,17
,,@incollection,aagaardolesen:2009,"Aagaard Olesen, Tonny",,,,,,2009,,The Young Kierkegaard on/as Faust.~The Systematic Study and the Existential Identification.~A Short Presentation,,cappelorn_nj-etal:2009,,,,,585--600,,,,,,,,,,,,,,,,,aesthetics,literary-criticism,,continental-philosophy,Kierkegaard,,,,,,,18
,,@book,aaker:1981,"Aaker, David A.",,,,,,1981,,Multivariate Analysis in Marketing,,,,,,,,,"Palo Alto, California",,"Scientific Press",,2,,,,,,,,,social-sciences,,,,,,,,,,,,,200000
,,@incollection,aalbers:2016,"Aalbers, Manuel B.",,,,,,2016,,Regulated Deregulation,,springer_s-etal:2016,,,,,563--573,,,,,,,,,,,,,,,,,political-philosophy,liberalism,neo-liberalism,,,,,,,19
,,@incollection,aalders-deblois:1992,"Aalders, H.~Wzn.~G.J.D. and De Blois, L.",,,,,,1992,,Plutarch und die politische Philosophie der Griechen,,haase_w:1992,,,,,3384--3404,,,,,,,,,,,,,,,,,political-philosophy,,ancient-philosophy,,,ngerman,,,20
,,@article,aall:1925,"Aall, Anathon",,,,,,1925,,The Problem of Reality: An Essay Concerning the Ultimate Forms of Existence,,,"The Journal of Philosophy",22,,533--547,,,,,,,,,,,,,,,,,metaphysics,ontological-categories,,,,,,,,21
,,@incollection,aaltola_e:2010,"Aaltola, Elisa",,,,,,2010,,Green Anarchy: Deep Ecology and Primitivism,,franks_b-wilson:2010,,,,,161--185,,,,,,,,,,,,,,,,,political-philosophy,anarchism,,,,,,,24
,,@book,aaltola_e:2012,"Aaltola, Elisa",,,,,,2012,,Animal Suffering: Philosophy and Culture,,,,,,,,,"Basingstoke, Hampshire",,"Palgrave Macmillan",,,,,,,,,,,animals,animal-ethics,,,,,,,,200001
,,@article,aaltola_e:2014,"Aaltola, Elisa",,,,,,2014,,Affective Empathy as Core Moral Agency: Psychopathy\, Autism and Reason Revisited,,"Philosophical Explorations",17,1,76--92,,,,,,,,,,,,,,,,,psychology,mental-illness,autism,,,,,,,25
,,@incollection,aanderaa:1971,"Aanderaa, St{\aa}l O.",,,,,,1971,,On the Decision Problem for Formulas in Which All Disjunctions Are Binary,,fenstad:1971,,,,,1--18,,,,,,,,,,,,,,,,,logic,(un)decidability,decidability,,,,,,,27
,,@incollection,aarnes:1991,"Aarnes, Asbj{\o}rn",,,,,,1991,,A Poet's Life and Work in the Perspective of Phenomenology,,tymieniecka:1991a,,,,,167--180,,,,,,,,,,,,,,,,,aesthetics,fiction,,,,,,,28
,,@book,aarnio_a:1983,"Aarnio, Aulis",,,,,,1983,,Philosophical Perspectives in Jurisprudence,,,,,36,,"Acta Philosophica Fennica",Helsinki,,"Societas Philosophica Fennica, Akateeminen Kirjakauppa",,,,,,,,,,,law,,,,,,,,,,,,,,200002
,,@incollection,aarnio_a:1984,"Aarnio, Aulis",,,,,,1984,,Paradigms in Legal Dogmatics Towards a Theory of Change and Progress in Legal Science,,peczenik-etal:1984,,,,,25--38,,,,,,,,,,,,,,,,,law,,,,,,,29
,,@book,aarnio_a:1987,"Aarnio, Aulis",,,,,,1987,,The Rational as Reasonable: A Treatise on Legal Justification,,,,,,,,Dordrecht,,"D.~Reidel Publishing Co.",,,,,,,,,,,law,,,,,,,,200003
,,@incollection,aarnio_a:1997,"Aarnio, Aulis",,,,,,1997,,On Precedents and their Bindingness,,garzonvaldes-etal:1997,,,,,,,,,,,,,,,,,,,,,,law,,,,,,,,,30
,,@incollection,aarnio_a:1999,"Aarnio, Aulis",,,,,,1999,,Law and Action: Reflections on Collective Legal Actions,,meggle:1999,,,,,37--54,,,,,,,,,,,,,,,,,action,collective-action,,,,,,,31
,,@article,aaron_ri-etal:1961,"Aaron, Richard Ithamar and Rotenstreich, Nathan and Passmore, John A. and Mercier, Andr{\'e} and Russell, Leonard J. and Moreau, Joseph",,,,,,1961,,Discussion sur \citet{hersch_j:1961} et \citet{marias:1961},,Dialectica,15,57/58,253--257,,,,,,,,,,,,,,,,dial.v15.i57-58.38,history,,,french,,,32
,,@article,aaron_ri:1931,"Aaron, Richard Ithamar",,,,,,1931,,Locke and Berkeley's Commonplace Book,,Mind,40,160,439--459,,,,,,,,,,,,,,,,,history-of-philosophy,,modern-philosophy,Locke,,,,,33
,,@article,aaron_ri:1933,"Aaron, Richard Ithamar",,,,,,1933,,Locke's Theory of Universals,,"Proceedings of the Aristotelian Society",33,,173--202,,,,,,,,,,,,,,,,,properties,universals,,modern-philosophy,Locke,,,,,34
,,@article,aaron_ri:1934,"Aaron, Richard Ithamar",,,,,,1934,,Is there an Element of Immediacy in Knowledge?,,"Proceedings of the Aristotelian Society, Supplementary Volume",13,,203--217,,,,,,,,,,,,,,,,,knowledge,,,,,,,,,35
,,@article,aaron_ri:1939,"Aaron, Richard Ithamar",,,,,,1939,,Two Senses of the Word ``Universal'',,Mind,48,,168--185,,,,,,,,,,,,,,,,,properties,universals,,,,,,,,,36
,,@article,aaron_ri:1939a,"Aaron, Richard Ithamar",,,,,,1939,,How May Phenomenalism Be Refuted?,,"Proceedings of the Aristotelian Society",39,,167--184,,,,,,,,,,,,,,,,,ontology,constructional-ontology,phenomenalism-as-ontology,,,,,,,37
,,@article,aaron_ri:1942,"Aaron, Richard Ithamar",,,,,,1942,,Hume's Theory of Universals,,"Proceedings of the Aristotelian Society",42,,117--140,,,,,,,,,,,,,,,,,properties,universals,,modern-philosophy,Hume,,,,,38
,,@article,aaron_ri:1945,"Aaron, Richard Ithamar",,,,,,1945,,The Causal Argument for Physical Objects,,"Proceedings of the Aristotelian Society, Supplementary Volume",19,,57--76,,,,,,,,,,,,,,,,,structuralism,structural-realism,ontic-structuralism,,,,,,,39
,,@article,aaron_ri:1946,"Aaron, Richard Ithamar",,,,,,1946,,Our Knowledge of Universals,,"Proceedings of the British Academy",31,,,,,,,,,,,,,,,,,,,properties,universals,,,,,,,,,,,,,40
,,@article,aaron_ri:1952,"Aaron, Richard Ithamar",,,,,,1952,,Dispensing with Mind,,"Proceedings of the Aristotelian Society",52,,225--242,,,,,,,,,,,,,,,,,mind,,,,,,,,,41
,,@article,aaron_ri:1956,"Aaron, Richard Ithamar",,,,,,1956,,Feeling Sure,,"Proceedings of the Aristotelian Society, Supplementary Volume",30,,1--13,,,,,,,,,,,,,,,,,epistemology,certainty,c&d,,,,,,,42
,,@incollection,aaron_ri:1956a,"Aaron, Richard Ithamar",,,,,,1956,,The Rational and the Empirical,,lewis_hd:1956,,,,,1--20,,,,,,,,,,,,,,,,,rationality,,,,,,,43
,,@article,aaron_ri:1957,"Aaron, Richard Ithamar",,,,,,1957,,The Common Sense View of Sense-Perception,,"Proceedings of the Aristotelian Society",58,,1--14,,,,,,,,,,,,,,,,,perception,,,,,,,,,44
,,@article,aaronson_bs:1971,"Aaronson, B.S.",,,,,,1971,,Time\, Time Stance\, and Existence,,"Studium Generale",24,,369--387,,,,,,,,,,"Reprinted in \citet[293--311]{fraser_jt-etal:1972}",,,,,,,time,ontology-of-time,,,,,,,45
,,@incollection,aaronson_s:2013,"Aaronson, Scott",,,,,,2013,,Why Philosophers should Care about Computational Complexity,,copeland_bj-etal:2013,,,,,261--328,,,,,,,,,,,,,,,,,computation,computability,,,,,,,46
,,@incollection,aars:1905,"Aars, Kristian Birch-Reichenwald",,,,,,1905,,Les hypoth{\`e}ses comme base des id{\'e}es g{\'e}n{\'e}rales et des abstractions,,claparede:1905,,,,,409--416,,,,,,,,,,,,,,,,,method,,,french,,,47
,,@incollection,aars:1909,"Aars, Kristian Birch-Reichenwald",,,,,,1909,,Abstraktion und Projektion,,elsenhans:1909,,,,,741--750,,,,,,,,,,,,,,,,,ontology,abstract-objects,abstraction,,ngerman,,,48
,,@article,aars:1910,"Aars, Kristian Birch-Reichenwald",,,,,,1910,,Platons Ideen als Einheiten,,"Archiv f{\"u}r Geschichte der Philosophie",23,4,518--531,,,,,,,,,,,,,,,,,properties,forms,Platonic-forms,ancient-philosophy,Plato,ngerman,,,49
,,@incollection,aarsleff:1994,"Aarsleff, Hans",,,,,,1994,,Locke's Influence,,chappell_vc:1994,,,,,252--289,,,,,,,,,,,,,,,,,history-of-philosophy,,modern-philosophy,Locke,,,50
,,@incollection,aarsleff:2006,"Aarsleff, Hans",,,,,,2006,,Philosophy of Language,,haakonssen:2006a,,,,,451--495,,,,,,,,,,,,,,,,,language,,modern-philosophy,,,,51
,,@book,aarts:1992,"Aarts, B.",,,,,,1992,,Small Clauses in English.~The Non-Verbal Types,,,,,,,,Berlin,,"de Gruyter Mouton",,,,,,,,,,,linguistics,,,,,,,,,,,,,,200004
,,@article,aasen:2016,"Aasen, Solveig",,,,,,2016,,Pictures\, Presence and Visibility,,"Philosophical Studies",173,1,187--203,,,,,,,,,,,,,,,,,representation,natural-meaning,pictorial-representation,,,,,,,53
,,@article,aasen:2016a,"Aasen, Solveig",,,,,,2016,,Visibility Constraints in Depiction: Objects Experienced versus Objects Depicted,,"The Philosophical Quarterly",66,265,665--679,,,,,,,,,,,,,,,,,representation,natural-meaning,pictorial-representation,,,,,,,54
,,@article,aasen:2017,"Aasen, Solveig",,,,,,2017,,Object-Dependent Thought Without Illusion,,"European Journal of Philosophy",25,1,68--84,,,,,,,,,,,,,,,,,representation,singular-thought,,,,,,,55"""


def clean_field_value(value: str) -> str:
    """Clean field values that aren't valid bibkeys or contain special strings."""
    if not value:
        return ""

    # Remove values that are clearly not bibkeys or valid field data
    invalid_patterns = [
        "ADD ENTRIES",
        "ENTRIES NOT NEEDED",
        "SOME ENTRIES ADDED",
        "ALL ENTRIES ADDED",
        "WP9-GET-DOI-FOR-BOOK-CHAPTER",
        "WP4-GET-PDF",
        "WP2-COLL:",
        "WP6-GET-PDF",
        "in file",
        "file",
    ]

    for pattern in invalid_patterns:
        if pattern in value:
            return ""

    # If it's a pure number (likely an ID), ignore it for bibkey fields
    if value.isdigit():
        return ""

    return value


def parse_csv_to_bibitem_data(csv_data: str) -> list[ParsedBibItemData]:
    """Convert CSV data to ParsedBibItemData objects."""
    entries = []
    reader = csv.DictReader(io.StringIO(csv_data))

    for row in reader:
        # Clean up problematic fields
        depends_on = clean_field_value(row.get("_depends_on", ""))
        further_refs = clean_field_value(row.get("_further_refs", ""))

        # Convert CSV row to ParsedBibItemData format
        entry: ParsedBibItemData = {}

        # Map all fields from CSV to ParsedBibItemData
        field_mapping = {
            "_to_do_general": "_to_do_general",
            "_change_request": "_change_request",
            "entry_type": "entry_type",
            "bibkey": "bibkey",
            "author": "author",
            "_author_ids": "_author_ids",
            "editor": "editor",
            "_editor_ids": "_editor_ids",
            "author_ids": "author_ids",
            "options": "options",
            "shorthand": "shorthand",
            "date": "date",
            "pubstate": "pubstate",
            "title": "title",
            "_title_unicode": "_title_unicode",
            "booktitle": "booktitle",
            "crossref": "crossref",
            "journal": "journal",
            "journal_id": "journal_id",
            "volume": "volume",
            "number": "number",
            "pages": "pages",
            "eid": "eid",
            "series": "series",
            "address": "address",
            "institution": "institution",
            "school": "school",
            "publisher": "publisher",
            "publisher_id": "publisher_id",
            "type": "type",
            "edition": "edition",
            "note": "note",
            "_issuetitle": "_issuetitle",
            "_guesteditor": "_guesteditor",
            "_extra_note": "_extra_note",
            "urn": "urn",
            "eprint": "eprint",
            "doi": "doi",
            "url": "url",
            "_kw_level1": "_kw_level1",
            "_kw_level2": "_kw_level2",
            "_kw_level3": "_kw_level3",
            "_epoch": "_epoch",
            "_person": "_person",
            "_comm_for_profile_bib": "_comm_for_profile_bib",
            "_langid": "_langid",
            "_lang_der": "_lang_der",
            "_dltc_num": "_dltc_num",
            "_spec_interest": "_spec_interest",
            "_note_perso": "_note_perso",
            "_note_stock": "_note_stock",
            "_note_status": "_note_status",
            "_num_inwork_coll": "_num_inwork_coll",
            "_num_inwork": "_num_inwork",
            "_num_coll": "_num_coll",
            "_dltc_copyediting_note": "_dltc_copyediting_note",
            "_note_missing": "_note_missing",
            "_num_sort": "_num_sort",
        }

        for csv_field, parsed_field in field_mapping.items():
            value = row.get(csv_field, "")
            if value:
                entry[parsed_field] = value  # type: ignore

        # Apply field cleaning for specific fields
        if "_further_refs" in entry:
            entry["_further_refs"] = further_refs
        if "_depends_on" in entry:
            entry["_depends_on"] = depends_on

        entries.append(entry)

    return entries


@pytest.fixture
def parsed_bibitem_entries() -> list[ParsedBibItemData]:
    """Provide parsed bibitem entries for testing."""
    return parse_csv_to_bibitem_data(CSV_BIBITEM_TEST_DATA)
