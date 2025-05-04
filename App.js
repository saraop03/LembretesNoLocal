
import React, { useEffect, useState } from 'react';
import { View, Text, Button, TextInput, StyleSheet, Platform } from 'react-native';
import * as Location from 'expo-location';
import * as Notifications from 'expo-notifications';
import MapView, { Marker } from 'react-native-maps';

export default function App() {
  const [location, setLocation] = useState(null);
  const [lembrete, setLembrete] = useState('');
  const [destino, setDestino] = useState({ latitude: '', longitude: '' });

  useEffect(() => {
    (async () => {
      await Location.requestForegroundPermissionsAsync();
      await Location.requestBackgroundPermissionsAsync();
      let loc = await Location.getCurrentPositionAsync({});
      setLocation(loc.coords);
    })();

    const interval = setInterval(verificarProximidade, 10000);
    return () => clearInterval(interval);
  }, []);

  const guardarLembrete = async () => {
    await fetch('http://<SEU_IP_LOCAL>:8000/lembretes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mensagem: lembrete,
        latitude: parseFloat(destino.latitude),
        longitude: parseFloat(destino.longitude),
      }),
    });
    alert('Lembrete guardado!');
  };

  const verificarProximidade = async () => {
    const loc = await Location.getCurrentPositionAsync({});
    const res = await fetch(`http://<SEU_IP_LOCAL>:8000/verificar/${loc.coords.latitude}/${loc.coords.longitude}`);
    const lembretesProximos = await res.json();

    lembretesProximos.forEach(lembrete => {
      Notifications.scheduleNotificationAsync({
        content: { title: 'Lembrete Próximo!', body: lembrete.mensagem },
        trigger: null,
      });
    });
  };

  return (
    <View style={styles.container}>
      <TextInput placeholder="Mensagem do Lembrete" onChangeText={setLembrete} style={styles.input} />
      <MapView
        style={{ height: 300 }}
        initialRegion={{ latitude: 41.1579, longitude: -8.6291, latitudeDelta: 0.01, longitudeDelta: 0.01 }}
        onPress={(e) => setDestino(e.nativeEvent.coordinate)}
      >
        {destino.latitude && (
          <Marker coordinate={{ latitude: parseFloat(destino.latitude), longitude: parseFloat(destino.longitude) }} />
        )}
      </MapView>
      <Button title="Guardar Lembrete" onPress={guardarLembrete} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, flex: 1, justifyContent: 'center' },
  input: { borderBottomWidth: 1, marginVertical: 8, padding: 6 },
});
