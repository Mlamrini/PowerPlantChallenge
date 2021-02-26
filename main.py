import json
from functools import cmp_to_key

from flask import Flask, request, abort

from powerplant import PowerPlant


def plan(data: dict):

    load_to_produce = data['load']
    fuels = data['fuels']
    plants = [PowerPlant.from_json(plant) for plant in data['powerplants']]

    # Step One : Sort plants by cost per MWh
    plants = sorted(
        plants,
        key=cmp_to_key(lambda a, b: compare_plants(a, b, fuels))
    )

    # Output containing adjusted loads by plant name
    load_distribution = dict()

    # List of retained plants
    loaded_plants = list()

    # Load to adjust to take into account plant starting power
    plants_to_recover = 0
    load_to_recover = 0

    # Step Two : Compute plant loads over global demand
    for plant in plants:
        if load_to_produce > 0:
            # Compute plant capacity and compare with demand
            plant_capacity = min(load_to_produce, plant.get_capacity(fuels))

            # If minimal power is sufficient, the load is computed over global demand
            if plant.minimal_power <= load_to_produce:
                # Only plants having a real capacity are retained
                # for example wind turbines without wind are excluded
                if plant_capacity > 0:
                    loaded_plants.append(plant)
                    load_to_produce -= plant_capacity
                    load_distribution[plant.name] = plant_capacity
                    plants_to_recover += 1
                else:
                    # Other plants are excluded from power generation
                    load_distribution[plant.name] = 0
            else:
                # When minimal power is an issue, the plant is added with minimal capacity
                # The exceeding load will be recovered in the next step
                if plants_to_recover > 0:
                    loaded_plants.append(plant)
                    load_to_recover = plant.minimal_power - load_to_produce
                    load_to_produce = 0
                    load_distribution[plant.name] = plant.minimal_power
                else:
                    load_distribution[plant.name] = 0
        else:
            # Total demand was already covered
            load_distribution[plant.name] = 0

    # If there is a load to recover, the distribution must be adjusted regarding plant starting power
    if load_to_recover > 0:
        loaded_plants.reverse()
        # Step Three : (optional) Recover exceeding power generation
        for plant in loaded_plants:
            if load_to_recover > 0:
                current_load = load_distribution[plant.name]

                # Current load can only be adjusted when minimal power is exceeded
                if current_load > plant.minimal_power:
                    plant_capacity = max(plant.minimal_power, load_distribution[plant.name] - load_to_recover)
                    load_distribution[plant.name] = plant_capacity
                    load_to_recover -= plant_capacity

    if load_to_produce > 0 or load_to_recover > 0:
        abort(400)

    return json.dumps(
        [{'name': key, 'p': value} for key, value in load_distribution.items()],
        indent=1
    )


def compare_plants(plant_one: PowerPlant, plant_two: PowerPlant, fuels: dict):
    plant_one_cost = plant_one.compute_cost(fuels)
    plant_two_cost = plant_two.compute_cost(fuels)

    if plant_one_cost == plant_two_cost:
        return plant_two.maximal_power - plant_one.maximal_power

    return plant_one_cost - plant_two_cost


app = Flask(__name__)


@app.errorhandler(400)
def page_not_found(error):
    return "The requested production cannot be planned", 400


@app.route('/productionplan', methods=['POST'])
def plan_production():
    return plan(request.json)


app.run(port=8888)
