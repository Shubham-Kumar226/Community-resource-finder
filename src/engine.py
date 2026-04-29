import os
import json
import math
from collections import Counter

from utils import clean_text, get_city_tag, normalize_category

class ResourceEngine:
    def __init__(self, data_paths=None):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.normpath(os.path.join(current_dir, ".."))
        self.data_paths = data_paths or [
            "data/resources.json",
            "data/community_resources_seed.json",
            "data/india_city_resources_seed.json",
            "data/transportation_resources_seed.json",
            "data/local_services_seed.json",
        ]
        if isinstance(self.data_paths, str):
            self.data_paths = [self.data_paths]

        self.resources = []
        for relative_path in self.data_paths:
            self.resources.extend(self._load_resources(relative_path))

        if not self.resources:
            raise FileNotFoundError("No community resource records were found.")

        self.categories = sorted({r["category"] for r in self.resources})
        self.cities = sorted({r["city"] for r in self.resources if r.get("city")})
        self.model = None
        self.resource_embeddings = None
        self.model_error = None
        self._prepare_semantic_index()

    def _load_resources(self, relative_path):
        data_path = os.path.normpath(os.path.join(self.root_dir, relative_path))
        if not os.path.exists(data_path):
            return []

        with open(data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        return [
            self._normalize_resource(record, data_path)
            for record in raw_data
            if record.get("name") and record.get("location")
        ]

    def _normalize_resource(self, record, data_path):
        name = str(record.get("name", "")).strip()
        location = str(record.get("location", "")).strip()
        category = normalize_category(record.get("category", "Community Resource"))
        city = (record.get("city") or self._infer_city(record, location, data_path)).strip()
        services = record.get("services") or []
        tags = record.get("tags") or []
        source = record.get("source") or os.path.basename(data_path)
        description = record.get("description") or (
            f"{name} is a {category.lower()} resource in {city}, located at {location}."
        )

        if isinstance(services, str):
            services = [services]
        if isinstance(tags, str):
            tags = [tags]

        searchable_text = " ".join(
            [
                name,
                category,
                city,
                location,
                description,
                " ".join(services),
                " ".join(tags),
            ]
        )

        return {
            "name": name,
            "location": location,
            "category": category,
            "city": city,
            "description": description,
            "services": services,
            "tags": tags,
            "phone": record.get("phone", "Verify locally"),
            "hours": record.get("hours", "Verify before visiting"),
            "cost": record.get("cost", "Varies"),
            "source": source,
            "lat": record.get("lat"),
            "lon": record.get("lon"),
            "_searchable_text": searchable_text,
        }

    def _infer_city(self, record, location, data_path):
        city = get_city_tag(location)
        if city != "City Facility":
            return city

        text = clean_text(
            " ".join(
                [
                    str(record.get("name", "")),
                    str(record.get("category", "")),
                    str(record.get("description", "")),
                    str(location),
                ]
            )
        )
        if any(word in text for word in ["bbmp", "bengaluru", "bangalore"]):
            return "Bengaluru"

        mumbai_areas = [
            "akurli",
            "andheri",
            "bandra",
            "borivali",
            "byculla",
            "chembur",
            "colaba",
            "dadar",
            "ghatkopar",
            "goregaon",
            "juhu",
            "kurla",
            "malad",
            "mulund",
            "parel",
            "sion",
            "thane",
            "vile parle",
            "wadala",
            "worli",
        ]
        if any(area in text for area in mumbai_areas):
            return "Mumbai"
        if os.path.basename(data_path) == "resources.json":
            return "Mumbai"
        return "City Facility"

    def _prepare_semantic_index(self):
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            descriptions = [r["_searchable_text"] for r in self.resources]
            self.resource_embeddings = self.model.encode(
                descriptions, convert_to_numpy=True, show_progress_bar=False
            )
        except Exception as exc:
            self.model_error = str(exc)
            self.model = None
            self.resource_embeddings = None

    def search(self, query, top_k=5, category="All", city="All", user_area=""):
        intent_query = clean_text(query)
        processed_query = intent_query
        user_area = (user_area or "").strip()
        if user_area:
            processed_query = clean_text(f"{processed_query} {user_area}")
        city_requested = city not in (None, "", "All")
        category_requested = category not in (None, "", "All")

        if city in (None, "", "All"):
            inferred_city = self._infer_city_from_query(intent_query)
            if inferred_city:
                city = inferred_city
                city_requested = True
        if category in (None, "", "All"):
            inferred_category = self._infer_category_from_query(intent_query)
            if inferred_category:
                category = inferred_category
                category_requested = True

        candidate_indexes = self._filter_indexes(category, city)
        if not candidate_indexes and city_requested and category_requested:
            candidate_indexes = self._filter_indexes("All", city)
        if not candidate_indexes:
            return []

        top_k = max(1, min(top_k, len(candidate_indexes)))
        search_k = min(len(candidate_indexes), max(top_k * 4, top_k))

        if self.model is not None and self.resource_embeddings is not None:
            results = self._semantic_search(processed_query, candidate_indexes, search_k)
        else:
            results = self._keyword_search(processed_query, candidate_indexes, search_k)

        results = self._boost_location_matches(results, user_area, top_k)
        return [self._with_coordinate_fallback(result) for result in results]

    def detect_city(self, query):
        return self._infer_city_from_query(clean_text(query))

    def _infer_city_from_query(self, query):
        city_aliases = {
            "Allahabad": ["allahabad", "allabhad", "prayagraj"],
            "Banaras": ["banaras", "benares", "varanasi", "kashi"],
            "Bengaluru": ["bengaluru", "bangalore"],
            "Bhopal": ["bhopal"],
            "Chennai": ["chennai", "madras"],
            "Delhi": ["delhi", "new delhi"],
            "Gaya": ["gaya"],
            "Lucknow": ["lucknow"],
            "Ludhiana": ["ludhiana", "ludhiyana"],
            "Madurai": ["madurai"],
            "Mangalore": ["mangalore", "mangaluru", "manglore", "mangalor"],
            "Mumbai": ["mumbai", "bombay"],
            "Patna": ["patna"],
            "Pune": ["pune"],
        }
        for city, aliases in city_aliases.items():
            if city in self.cities and any(alias in query for alias in aliases):
                return city
        return None

    def _infer_category_from_query(self, query):
        category_aliases = [
            ("Salons", ["salon", "salons", "saloon", "saloons", "barber", "beauty", "parlour", "parlor"]),
            ("Mechanics", ["mechanic", "mechanics", "garage", "repair", "puncture", "vehicle", "bike repair", "car repair"]),
            ("Clothes", ["clothes", "cloth", "clothing", "garment", "apparel", "tailor", "dress"]),
            ("Sweet Shops", ["sweet", "sweets", "mithai", "bakery", "dessert"]),
            ("Stationery", ["stationery", "stationary", "book", "notebook", "xerox", "print", "printing", "pen"]),
            ("Groceries", ["grocery", "groceries", "grocerries", "grocerry", "kirana", "ration", "general store", "vegetables", "milk"]),
            (
                "Transportation",
                [
                    "transport",
                    "bus",
                    "busstand",
                    "bus stand",
                    "metro",
                    "rail",
                    "train",
                    "station",
                    "cab",
                    "taxi",
                    "auto",
                    "pickup",
                    "stand",
                ],
            ),
            ("Doctors", ["doctor", "doctors", "physician", "pediatrician", "cardiologist"]),
            ("Hospital", ["hospital", "clinic", "medical", "emergency"]),
            ("Free Food", ["free food", "free meal", "langar", "meal", "food help", "canteen"]),
            ("NGO", ["ngo", "volunteer", "charity", "foundation", "donation"]),
            ("Mall", ["mall"]),
            ("Shops", ["shop", "shops", "shopping", "market", "groceries", "store"]),
        ]
        for category, aliases in category_aliases:
            if category in self.categories and any(alias in query for alias in aliases):
                return category
        return None

    def _filter_indexes(self, category, city):
        selected = []
        for index, resource in enumerate(self.resources):
            category_match = category in (None, "", "All") or resource["category"] == category
            city_match = city in (None, "", "All") or resource["city"] == city
            if category_match and city_match:
                selected.append(index)
        return selected

    def _boost_location_matches(self, results, user_area, top_k):
        area_terms = [
            term
            for term in clean_text(user_area).split()
            if len(term) > 2 and term not in {"near", "road", "area"}
        ]
        if not area_terms:
            return results[:top_k]

        ranked = []
        for order, resource in enumerate(results):
            text = clean_text(
                " ".join(
                    [
                        resource.get("name", ""),
                        resource.get("location", ""),
                        resource.get("description", ""),
                        " ".join(resource.get("services", [])),
                        " ".join(resource.get("tags", [])),
                    ]
                )
            )
            boost = sum(1 for term in area_terms if term in text)
            score = float(resource.get("_score", 0)) + (boost * 0.35) - (order * 0.0001)
            boosted_resource = dict(resource)
            boosted_resource["_score"] = score
            ranked.append((score, boosted_resource))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [resource for _, resource in ranked[:top_k]]

    def _semantic_search(self, query, candidate_indexes, top_k):
        from sentence_transformers import util

        query_embedding = self.model.encode(query, convert_to_numpy=True)
        candidate_embeddings = self.resource_embeddings[candidate_indexes]
        hits = util.semantic_search(query_embedding, candidate_embeddings, top_k=top_k)[0]
        results = []
        for hit in hits:
            resource = dict(self.resources[candidate_indexes[hit["corpus_id"]]])
            resource["_score"] = float(hit["score"])
            results.append(resource)
        return results

    def _keyword_search(self, query, candidate_indexes, top_k):
        query_terms = Counter(clean_text(query).split())
        scored = []
        for index in candidate_indexes:
            resource = self.resources[index]
            text = clean_text(resource["_searchable_text"])
            terms = Counter(text.split())
            overlap = sum(min(query_terms[t], terms[t]) for t in query_terms)
            phrase_bonus = 2 if query and query in text else 0
            category_bonus = 1.5 if resource["category"].lower() in query else 0
            city_bonus = 1 if resource["city"].lower() in query else 0
            score = overlap + phrase_bonus + category_bonus + city_bonus
            normalized = score / math.sqrt(max(1, len(terms)))
            scored.append((normalized, index))

        scored.sort(reverse=True)
        results = []
        for score, index in scored[:top_k]:
            resource = dict(self.resources[index])
            resource["_score"] = float(score)
            results.append(resource)
        return results

    def _with_coordinate_fallback(self, resource):
        if resource.get("lat") and resource.get("lon"):
            return resource

        if resource.get("city") == "Mumbai":
            resource["lat"], resource["lon"] = 19.0760, 72.8777
        elif resource.get("city") == "Bengaluru":
            resource["lat"], resource["lon"] = 12.9716, 77.5946
        else:
            resource["lat"], resource["lon"] = 20.5937, 78.9629
        return resource
