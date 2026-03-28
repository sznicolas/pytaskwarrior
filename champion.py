import uuid

from taskchampion import Operations, Replica, Status


def init_rep_disk(datapath: str, create_if_missing: bool=True) -> Replica :
# Initialiser la réplique
    return Replica.new_on_disk(datapath, create_if_missing=create_if_missing)

def init_rep_mem() -> Replica :
    # Initialiser la réplique
    return Replica.new_in_memory()

# Créer un objet Operations (pas une liste)

def create_task(replica, desc) -> Operations:
# Créer la tâche
    ops = Operations()
    task_uuid = str(uuid.uuid4())
    task = replica.create_task(task_uuid, ops)

    # Définir la description
    task.set_description("Ma nouvelle tâche", ops)

    # Mettre à jour le statut (cela ajoute automatiquement une ou plusieurs opérations à `ops`)
    task.set_status(Status.Pending, ops)
    return ops

def commit(replica, ops):
    # Appliquer les opérations
    return replica.commit_operations(ops)
