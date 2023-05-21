import json
import logging
from typing import Any, Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

Observer = Callable[[dict[str, Any]], None]


class MqttClient:
    """MQTT message handler.

    Args:
        host: Hostname of the MQTT broker.
        port: Port number of the MQTT broker.
        protocol: MQTT client version.
        auth: Username/password for broker authentication.
        client_id: Name of the MQTT client (must be unique to this instance).

    """

    def __init__(
        self,
        host: str,
        port: int = 1883,
        protocol: int = mqtt.MQTTv311,
        auth: tuple[str, str] | None = None,
        client_id: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self._observers: set[Observer] = set()

        self.client = mqtt.Client(client_id, protocol=protocol)
        self.client.enable_logger()
        if auth is not None:
            self.client.username_pw_set(*auth)

        # Internal MQTT callback functions
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def connect(self) -> None:
        """Establish an MQTT connection to a remote broker."""
        if self.is_connected():
            logger.debug("MQTT client is already connected.")
            return None

        logger.debug("Establishing connection to MQTT client.")
        self.client.connect(self.host, self.port)
        self.client.loop_start()

    def disconnect(self) -> None:
        """Disconnect a connected MQTT client from the broker."""
        if not self.is_connected():
            logger.debug("MQTT client is already disconnected.")
            return None

        logger.debug("Disconnecting from MQTT client.")
        self.client.loop_stop()
        self.client.disconnect()

    def is_connected(self) -> bool:
        """Check current connection status.

        Returns:
            True if connection exists.

        """
        return self.client.is_connected()

    def publish(self, topic: str, message: dict[str, Any], qos: int = 0) -> None:
        """Publish a message to a topic.

        Args:
            topic: Name of topic to subscribe to.
            message: Message to send.
            qos: Quality of service level.

        """
        result = self.client.publish(topic, json.dumps(message), qos=qos)
        result.wait_for_publish()

    def subscribe(self, topic: str, qos: int = 0) -> None:
        """Subscribe to a topic.

        Args:
            topic: Name of topic to subscribe to.
            qos: Quality of service level.

        """
        self.client.subscribe(topic, qos=qos)

    def observe(self, observer: Observer) -> None:
        """Add an observer."""
        logger.debug(f"Start observing: {observer.__name__}")
        self._observers.add(observer)

    def unobserve(self, observer: Observer) -> None:
        """Remove an observer."""
        logger.debug(f"Stop observing: {observer.__name__}")
        self._observers.remove(observer)

    def _on_message(self, client: mqtt.Client, userdata: None, message: mqtt.MQTTMessage) -> None:
        """Internal callback function that gets called when an MQTT message is received."""
        logger.info(f"Handled message: {message.topic}: {str(message.payload)}")
        payload = json.loads(message.payload)
        # Notify the consumers
        for observer in self._observers:
            observer(payload)

    @staticmethod
    def _on_connect(client: mqtt.Client, userdata: None, flags: object, rc: int) -> None:
        """Internal callback function called when an MQTT connection is established."""
        logger.debug(f"Result from connect: {mqtt.connack_string(rc)}")
        if rc != mqtt.CONNACK_ACCEPTED:
            logger.exception(f"Unable to connect to MQTT Broker: {rc}")
            raise Exception
        logger.info("Connected to MQTT Broker")

    @staticmethod
    def _on_disconnect(client: mqtt.Client, userdata: None, rc: int) -> None:
        """Internal callback function called when an MQTT connection is disconnected."""
        logger.debug(f"Result from disconnect: {mqtt.connack_string(rc)}")
        if rc != mqtt.CONNACK_ACCEPTED:
            logger.exception(f"Unable to disconnect from MQTT Broker: {rc}")
            raise Exception
        logger.info("Disconnected from MQTT Broker")
