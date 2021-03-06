from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.http import JsonResponse
from partida.models import *
from usuario.models import Usuario
from django.contrib.auth.models import User
from .forms import FormularioPartida
from django.http import HttpResponseRedirect
from partida.funciones_auxs import *
import os, shutil
import glob
from partida.define import ListaDeDescipcionDePiezas
from django.core import serializers
from partida.funciones_auxs import compatibilidad_juego
# Create your views here.

@login_required
def lista_de_partidas(request):
    usuario = Usuario.objects.get(usuario=request.user.id)
    # si estaba jugando una partida ya no lo esta asi que lo desunimos de la partida que estaba unido
    usuario.partida = None
    usuario.turno = 0
    usuario.save()
    partidas = Partida.objects.all()
    # asignamos a las partidas las cantidad actual de jugadores que estan esperando por jugarlas
    for partida in partidas:
        partida.jugando = Usuario.objects.filter(partida=partida).count()
        partida.save()
    #Partida.objects.all().delete()
 
    return render(request, 'lista_de_partidas.html',
                  {'partidas': partidas})


@login_required
def unirse_a_partida(request, pk):
    partida = Partida.objects.get(pk=pk)
    usuario = Usuario.objects.get(usuario=request.user.id)
    # asignamos el turno del actual jugador como la cantidad de jugadores jugando (esperando jugar) mas 1
    # ya que si estamos en esta funcion se cumple partida.jugando < partida.cantidad_jugadores
    # y el turno se asgina por orden de llegada, es decir, el que se unio ultimo a la partida juega ultimo
    # y asi
    #sino tiene asignado turno se lo asignamos
    print("usuario.turno unirse_a_partida ANTEs")
    print(usuario.turno)
    if usuario.turno == 0:
        usuario.turno = partida.jugando + 1

    # unimos el usuario a la partida
    print("usuario.turno en unirse_a_partida")
    print(usuario.turno)
    usuario.partida = partida
    usuario.save()
    # actualiazmos la cantidad de jugadores que estan jugando la partida
    partida.jugando = Usuario.objects.filter(partida=partida).count()
    partida.save()
    if partida.jugando != partida.cantidad_jugadores:
        return render(request,'unirse_a_partida.html', {partida : 'partida'})
    else:
        return redirect('jugar_partida') 


@login_required
def abandonar_partida(request, pk):
    partida = Partida.objects.get(pk=pk)
    usuario = Usuario.objects.get(usuario=request.user.id)
    # desunimos el usuario a la partida
    usuario.partida = None
    # reseteamos el turno del usuario
    usuario.turno = 0
    usuario.save()
    # actualiazmos la cantidad de jugadores que estan jugando la partida
    partida.jugando = Usuario.objects.filter(partida=partida).count()
    partida.save()
    return redirect('lista_de_partidas') 

@login_required
def jugar_partida(request):
    current_user = Usuario.objects.get(usuario=request.user.id)
    partida = current_user.partida
    # devuelve los usuarios que estan jugando los partidas
    usuarios = Usuario.objects.filter(partida=partida)
    hubo_posteo = 0
    posteo_invalido = 0
    if current_user.turno == partida.turnos:
        if request.method == 'POST':
            hubo_posteo = 1
            # par (x,y) que describe la posicion de la ficha en el mapa de esta partida
            pos_x = request.POST["pos_x"]
            pos_y = request.POST["pos_y"]
            # cant_giros para saber el grado con el que el usuario quizo girar la imagen (si es que quiso)
            # ej cant_giros = 5 --> 450 grados
            # ej cant_giros = 1 --> 90 grados
            # ej cant_giros = -1 --> 360-90 grados
            
            cant_giros = request.POST["cant_giros"]
            pos_x = int(pos_x)
            pos_y = int(pos_y)

            # aca se deberia llamar a la funcion de rotar_imagen
            if cant_giros != '' and int(cant_giros) > -1:
                rotarpieza(partida.pieza_en_juego, cant_giros)

            # si el usuario no coloco algun dato del posteo necesario
            if pos_x == '' or pos_y == '':
                print("uno")
                posteo_invalido = 1
            # si la posicion ingresada no pertenecen a la matriz    
            elif pos_x < 0 or pos_y < 0 or pos_x > 59 or pos_y > 59:
                print("unoss")

                posteo_invalido = 1
            # si ya hay una ficha en la posicion ingresada 
            elif Pieza.objects.filter(partida=partida,pos_x=pos_x,pos_y=pos_y).exists():
                print("unodasdad")

                posteo_invalido = 1
            else:
                # se forman los lados de la pieza que tendria x,y de colocarse definitivamente
                lados_de_pieza = lados_pieza(partida.pieza_en_juego)
                # se verifica que la pieza colocada en tal ubicacion (x,y) es valida para las normas
                # del juego
                posteo_invalido = compatibilidad_juego(pos_x,pos_y,lados_de_pieza,partida)
                print(posteo_invalido)
            # si el posteo es valido aumentamos el turno, para que juege el proximo jugador
            if posteo_invalido == 0:
                print ("TURNOOOOOOOOOOOOOOOOO") 
                if partida.turnos < partida.cantidad_jugadores:
                    partida.turnos = partida.turnos + 1
                else:
                    partida.turnos = 1

    # si hubo posteo y es valido, agregamos la pieza introducida por el usuario con los giros
    # que tuviera y pasamos el turno              
    if hubo_posteo == 1 and posteo_invalido == 0:
        print("acaa2")
        partida.save()
        return redirect('jugar_partida')
     
    # de lo contrario:
    # si hubo posteo pero invalido, se lo redirige a la misma pag para que trate de introducir nuevamente 
    # la misma ficha
    elif hubo_posteo == 1 and posteo_invalido == 1:
        print("acaa")
        piezaid = partida.pieza_en_juego
        partida = current_user.partida
        partida.pieza_en_juego = piezaid
        partida.save()
        turno = partida.turnos
        piezas = Pieza.objects.filter(partida=partida)
        piezas = serializers.serialize("json", piezas)

        print("TURNO DESPUES")
        print(turno)
        jugadores = User.objects.filter(usuario__partida=partida)
        context = {
            'jugadores' : jugadores,
            'current_user' : current_user,
            'turno' : turno,
            'piezas' : piezas,
            'piezaid' : piezaid
        }
        return render(request,'jugar_partida.html', context) 

    # si no hubo posteo, se le da una pieza por hacer
    else:
        #aca deberia llamarse a una funcion que toma un valor random, de numero, para elegir la foto azarosamente
        piezaid = 23
        partida = current_user.partida
        partida.pieza_en_juego = piezaid
        partida.save()
        turno = partida.turnos
        piezas = Pieza.objects.filter(partida=partida)
        piezas = serializers.serialize("json", piezas)
        print(piezas)
        print("TURNO DESPUES")
        print(turno)
        jugadores = User.objects.filter(usuario__partida=partida)
        context = {
            'jugadores' : jugadores,
            'current_user' : current_user,
            'turno' : turno,
            'piezas' : piezas,
            'piezaid' : piezaid
        }
        return render(request,'jugar_partida.html', context) 



@login_required
def crear_partida(request):
    if request.method == "POST":
        form = FormularioPartida(request.POST)
        if form.is_valid():
            partida = form.save(commit=False)
            usuario = Usuario.objects.get(usuario=request.user.id)
            partida.save()
            usuario.partida = partida
            usuario.save()
            path = '../static/partida' + str(partida.pk) + "/"
            # algo asi.. es decir crear un subdirectorio static/partidapk donde
            # estan todas las imagenes de las piezas
            #shutil.copytree('../static/piezas',path)
            manejodedirectorio(partida.pk)
            for x in range(1, 72):
              if x < 10:
                piezanueva = Pieza(esDescartada=False,
                                   lado1 = ListaDeDescipcionDePiezas[x - 1][0],
                                   lado2 = ListaDeDescipcionDePiezas[x - 1][1],
                                   lado3 = ListaDeDescipcionDePiezas[x - 1][2],
                                   lado4 = ListaDeDescipcionDePiezas[x - 1][3],
                                   idp = x,
                                   pathimagen = path + '0' + str(x) + '.png' )
              else :
                piezanueva = Pieza(esDescartada=False,
                                   lado1 = ListaDeDescipcionDePiezas[x - 1][0],
                                   lado2 = ListaDeDescipcionDePiezas[x - 1][1],
                                   lado3 = ListaDeDescipcionDePiezas[x - 1][2],
                                   lado4 = ListaDeDescipcionDePiezas[x - 1][3],
                                   idp = x,
                                   pathimagen = path +  str(x) + '.png' )
              piezanueva.save()
              return redirect( 'unirse_a_partida',pk=partida.pk)
    else:
        form = FormularioPartida()

    return render(request, 'crear_partida.html', {'form': form})

