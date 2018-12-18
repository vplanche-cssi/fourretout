#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# Copyright 2017-2018 CS Systemes d'Information (CS SI)
# All rights reserved

import time
from xml.sax.saxutils import escape

import requests

import pywps
from pywps import Process, ComplexOutput, ComplexInput, Format, BoundingBoxInput, LiteralInput
from .lib.helpers import getlogger

import socket
import json
import os, tempfile

from pywps.response.status import WPS_STATUS
from .lib.bbox_helpers import bbox_from_bboxinput
import docker

LOGGER = getlogger("bidsraf")
HOST_MOUNT_POINT = pywps.configuration.get_config_value("bidsraf", "data_mount_point")
# SPARK_MASTER_IP = pywps.configuration.get_config_value("bidsraf", "spark_master_ip")
#SPARK_MASTER_IP = os.environ['SPARKMASTER_IP']

class S2P(Process):
    def __init__(self):
        inputs = [
            BoundingBoxInput('bbox_in', 'ROI to process', ['epsg:4326', 'epsg:3035']),
            LiteralInput('platform_id', 'Satellite Platform. ex: PLEIADES-1B',
                         data_type='string', min_occurs=0, max_occurs=10),
            # ComplexInput(identifier='work',
            #              title='Input work parameters',
            #              abstract='Parametres du chantier a produire au format XML',
            #              supported_formats=[Format('text/xml', extension='.xml'), ]),
        ]
        outputs = [
            # ComplexOutput('outdatafile','Output data',supported_formats=[Format(mime_type="application/tar"), Format(mime_type="application/tar+gzip")]),
            ComplexOutput('outdatafile', 'Output data', supported_formats=[Format(mime_type="application/json")]),
            # LiteralOutput('outdata','Output data',data_type='string'),
        ]

        super(S2P, self).__init__(
            self._handler,
            identifier='S2P',
            version='0.2',
            title="BIDSRAF Demo with S2P",
            abstract="""BIDSRAF demo: process s2p on roi""",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        LOGGER.info("Executing BIDSRAF demo")

        # Ensure workdir exist
        os.makedirs(self.workdir, exist_ok=True)

        LOGGER.info("Launching docker eodag with ROI")
        bbox = request.inputs['bbox_in'][0]
        if 'platform_id' in request.inputs:
            self._platform_id = [p.data for p in request.inputs.get('platform_id')]
        else:
            self._platform_id = None
        self._make_docker_options(bbox)
        self._launch_eodag(response)

        results = self._launch_s2p(response)

        outfilename = os.path.join(tempfile.gettempdir(), "BIDSRAF_" + str(self.uuid) + ".json")
        LOGGER.debug("OUT filename: {}".format(outfilename))
        with open(outfilename, "w") as out:
            s = json.dumps(results, ensure_ascii=False)
            out.write(s)

        response.outputs['outdatafile'].set_file(outfilename)
        return response

    def _make_docker_options(self, bbox):
        b = bbox_from_bboxinput(bbox)
        self._bboxoption = 'Z' + ','.join(list(map(str, [b.minx,
                                                         b.miny,
                                                         b.maxx,
                                                         b.maxy])))


    def _launch_eodag(self, response):
        LOGGER.debug("Launching EODAG")
        response._update_status(message='Launching EODAG', status_percentage=1, status=WPS_STATUS.STARTED)

        # Create specific working dir
        products_dir = '/shared/data/products'
        work_dir = os.path.join('/shared/data', os.path.basename(self.workdir))
        os.makedirs(work_dir, exist_ok =True)

        # Evironment option
        env_opt = {}
        env_opt.update({'bbox': self._bboxoption})
        if self._platform_id:
            env_opt.update({'platform_id': ','.join(self._platform_id)})

        client = docker.from_env()
        #container = client.containers.run("bidsraf/eodag",
        #                                  volumes={os.path.join(HOST_MOUNT_POINT,
        #                                                        os.path.basename(self.workdir)):
        #                                               {'bind': '/tmp/bidsrafeodag', 'mode': 'rw'},
        #                                               '/shared/data/secrets/eodag-user-cfg.yaml':
        #                                               {'bind': '/etc/eodag/eodag-user-cfg.yaml', 'mode': 'ro'}},
        #                                  environment=env_opt,
        #                                  stdout=True, stderr=True,
        #                                  auto_remove=False,
        #                                  detach=True
        #                                  )
        container = client.containers.run("bidsraf/eodag",
                                          volumes={products_dir: {'bind': '/tmp/bidsrafeodag', 'mode': 'rw'},
                                                   '/shared/data/secrets/eodag-user-cfg.yaml': {'bind': '/etc/eodag/eodag-user-cfg.yaml', 'mode': 'ro'}},
                                          environment=env_opt,
                                          stdout=True, stderr=True,
                                          auto_remove=True,
                                          detach=True
                                          )
        while True:
            container_log = container.logs(stdout=True, stderr=True, tail=5).decode("utf-8")
            LOGGER.debug("Retrieved log from eodag : {}".format(container_log))
            response._update_status(message=escape(container_log), status_percentage=2, status=WPS_STATUS.STARTED)
            try:
                client.containers
                container_status = container.wait(timeout=5)
                if container_status == 0:
                    break
                # raise Exception('Something went wrong with eodag')
                LOGGER.warn("EODAG exited with status code {}".format(container_status))
                break
            except requests.exceptions.ReadTimeout:
                pass
            except requests.exceptions.ConnectionError:
                pass
            except socket.timeout:
                pass
            # except requests.packages.urllib3.exceptions.ReadTimeoutError:
            #     pass

    def _launch_s2p(self, response):
        LOGGER.info("Calling S2P")
        response._update_status(message='Calling S2P', status_percentage=5,
                                status=WPS_STATUS.STARTED)

        client = docker.from_env()
        container = client.containers.run("bidsraf/s2p",
                                          network="net-spark",
                                          volumes={"/shared/data":
                                                       {'bind': '/shared/data', 'mode': 'rw'},
                                                   '/shared/data/secrets/tenants.toml':
                                                       {'bind': '/etc/safescale/tenants.toml'},
                                                   '/shared/data/safescale/features':
                                                       {'bind': '/etc/safescale/features'}},
                                          command="s2p /shared/data/products {}".format("bidsraf-sparkmaster"),
                                          stdout=True, stderr=True,
                                          auto_remove=False,
                                          detach=True
                                          )
        while True:
            container_log = container.logs(stdout=True, stderr=True, tail=1).decode("utf-8")
            LOGGER.debug("Retrieved log from s2p : {}".format(container_log))
            response._update_status(message=escape(container_log), status_percentage=2,
                                    status=WPS_STATUS.STARTED)

            try:
                client.containers
                container_status = container.wait(timeout=5)
                if container_status == 0:
                    break
                # raise Exception('Something went wrong with eodag')
                LOGGER.warn("S2P exited with status code {}".format(container_status))
                break
            except requests.exceptions.ReadTimeout:
                pass
            except requests.exceptions.ConnectionError:
                pass
            except socket.timeout:
                pass
            # except requests.packages.urllib3.exceptions.ReadTimeoutError:
            #     pass

        results = """{"bidsraf":"plop"}"""
        return results
